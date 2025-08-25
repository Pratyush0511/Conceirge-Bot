"""
Document processing service for PDF extraction and indexing
"""

import os
try:
    import PyPDF2
    PDF_AVAILABLE = True
except ImportError:
    PDF_AVAILABLE = False
    PyPDF2 = None
import uuid
from typing import List, Dict, Optional, Tuple
from werkzeug.utils import secure_filename
from app.models.mongo_models import Document, DocumentChunk
import json

try:
    from sentence_transformers import SentenceTransformer
    import faiss
    import numpy as np
    EMBEDDINGS_AVAILABLE = True
except ImportError:
    EMBEDDINGS_AVAILABLE = False
    SentenceTransformer = None
    faiss = None
    np = None

class DocumentService:
    def __init__(self):
        self.upload_folder = os.path.join(os.getcwd(), 'uploads', 'documents')
        self.allowed_extensions = {'pdf', 'txt', 'doc', 'docx'}
        self.chunk_size = 1000
        self.chunk_overlap = 200
        
        # Create upload directory
        os.makedirs(self.upload_folder, exist_ok=True)
        
        # Initialize embedding model if available
        if EMBEDDINGS_AVAILABLE:
            try:
                self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
                self.dimension = 384  # Dimension of all-MiniLM-L6-v2
                self.embeddings_available = True
            except Exception:
                self.embedding_model = None
                self.embeddings_available = False
        else:
            self.embedding_model = None
            self.embeddings_available = False
    
    def allowed_file(self, filename: str) -> bool:
        """Check if file extension is allowed"""
        return '.' in filename and \
               filename.rsplit('.', 1)[1].lower() in self.allowed_extensions
    
    def extract_text_from_pdf(self, file_path: str) -> Tuple[str, List[Dict]]:
        """Extract text from PDF file"""
        if not PDF_AVAILABLE:
            raise Exception("PyPDF2 not available. Please install with: pip install PyPDF2")
        
        try:
            with open(file_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                text_content = ""
                pages_info = []
                
                for page_num, page in enumerate(pdf_reader.pages):
                    page_text = page.extract_text()
                    text_content += page_text + "\n"
                    pages_info.append({
                        'page_number': page_num + 1,
                        'text': page_text,
                        'char_start': len(text_content) - len(page_text) - 1,
                        'char_end': len(text_content) - 1
                    })
                
                return text_content, pages_info
        except Exception as e:
            raise Exception(f"Error extracting text from PDF: {str(e)}")
    
    def chunk_text(self, text: str, pages_info: List[Dict]) -> List[Dict]:
        """Split text into chunks for better processing"""
        chunks = []
        words = text.split()
        
        current_chunk = []
        current_length = 0
        chunk_index = 0
        
        for word in words:
            if current_length + len(word) + 1 > self.chunk_size and current_chunk:
                # Create chunk
                chunk_text = ' '.join(current_chunk)
                chunk_start = text.find(chunk_text)
                chunk_end = chunk_start + len(chunk_text)
                
                # Find page number for this chunk
                page_number = 1
                for page_info in pages_info:
                    if chunk_start >= page_info['char_start'] and chunk_start <= page_info['char_end']:
                        page_number = page_info['page_number']
                        break
                
                chunks.append({
                    'index': chunk_index,
                    'content': chunk_text,
                    'start_char': chunk_start,
                    'end_char': chunk_end,
                    'page_number': page_number
                })
                
                # Start new chunk with overlap
                overlap_words = current_chunk[-self.chunk_overlap//10:] if len(current_chunk) > self.chunk_overlap//10 else []
                current_chunk = overlap_words + [word]
                current_length = sum(len(w) + 1 for w in current_chunk)
                chunk_index += 1
            else:
                current_chunk.append(word)
                current_length += len(word) + 1
        
        # Add final chunk
        if current_chunk:
            chunk_text = ' '.join(current_chunk)
            chunk_start = text.find(chunk_text)
            chunk_end = chunk_start + len(chunk_text)
            
            page_number = 1
            for page_info in pages_info:
                if chunk_start >= page_info['char_start'] and chunk_start <= page_info['char_end']:
                    page_number = page_info['page_number']
                    break
            
            chunks.append({
                'index': chunk_index,
                'content': chunk_text,
                'start_char': chunk_start,
                'end_char': chunk_end,
                'page_number': page_number
            })
        
        return chunks
    
    def generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for text chunks"""
        if not self.embedding_model:
            return [[] for _ in texts]
        
        try:
            embeddings = self.embedding_model.encode(texts)
            return embeddings.tolist()
        except Exception:
            return [[] for _ in texts]
    
    def upload_document(self, file, category: str = 'policy', title: str = '', 
                       description: str = '', uploaded_by: str = 'admin') -> Document:
        """Upload and process a document"""
        if not file or not self.allowed_file(file.filename):
            raise ValueError("Invalid file type")
        
        # Generate unique filename
        file_id = str(uuid.uuid4())
        filename = secure_filename(file.filename)
        file_extension = filename.rsplit('.', 1)[1].lower()
        new_filename = f"{file_id}.{file_extension}"
        file_path = os.path.join(self.upload_folder, new_filename)
        
        # Save file
        file.save(file_path)
        file_size = os.path.getsize(file_path)
        
        # Create document record
        document_data = {
            '_id': file_id,
            'filename': new_filename,
            'original_filename': filename,
            'file_path': file_path,
            'file_size': file_size,
            'mime_type': file.content_type,
            'category': category,
            'title': title or filename,
            'description': description,
            'uploaded_by': uploaded_by,
            'upload_date': datetime.utcnow(),
            'is_active': True
        }
        mongo.db.documents.insert_one(document_data)
        document = Document.from_dict(document_data)
        
        # Process document asynchronously
        try:
            self.process_document(document.id)
        except Exception as e:
            print(f"Error processing document: {e}")
        
        return document
    
    def process_document(self, document_id: str) -> bool:
        """Process document: extract text, create chunks, generate embeddings"""
        document_data = mongo.db.documents.find_one({'_id': document_id})
        if not document_data:
            return False
        document = Document.from_dict(document_data)

        # Delete existing chunks for this document
        mongo.db.document_chunks.delete_many({'document_id': document_id})

        file_path = document.file_path
        file_extension = document.original_filename.rsplit('.', 1)[1].lower()

        text_content = ""
        pages_info = []

        if file_extension == 'pdf':
            text_content, pages_info = self.extract_text_from_pdf(file_path)
        elif file_extension in ['txt', 'doc', 'docx']:
            with open(file_path, 'r', encoding='utf-8') as f:
                text_content = f.read()
            pages_info = [{'page_number': 1, 'text': text_content, 'char_start': 0, 'char_end': len(text_content)}]
        else:
            print(f"Unsupported file type for processing: {file_extension}")
            return False

        chunks = self.chunk_text(text_content, pages_info)
        chunk_contents = [chunk['content'] for chunk in chunks]
        embeddings = self.generate_embeddings(chunk_contents)

        # Store chunks in MongoDB
        for i, chunk in enumerate(chunks):
            chunk_data = {
                '_id': str(uuid.uuid4()),
                'document_id': document.id,
                'chunk_index': chunk['index'],
                'content': chunk['content'],
                'embedding': embeddings[i],
                'page_number': chunk['page_number'],
                'start_char': chunk['start_char'],
                'end_char': chunk['end_char']
            }
            mongo.db.document_chunks.insert_one(chunk_data)

        return True

    def query_documents(self, query_text: str, top_k: int = 5) -> List[Dict]:
        if not self.embeddings_available:
            print("Embeddings not available. Cannot query documents.")
            return []

        query_embedding = self.embedding_model.encode([query_text])[0].tolist()

        # Find similar documents using vector search (requires MongoDB Atlas Search with Vector Search enabled)
        # This is a placeholder for a more robust vector search implementation
        # For local MongoDB, you might need to fetch all and calculate similarity in Python

        # For demonstration, we'll fetch all documents and calculate similarity (less efficient for large datasets)
        all_chunks = list(mongo.db.document_chunks.find({}))
        
        # Calculate cosine similarity
        similarities = []
        for chunk in all_chunks:
            if 'embedding' in chunk and chunk['embedding']:
                chunk_embedding = np.array(chunk['embedding'])
                q_embedding = np.array(query_embedding)
                similarity = np.dot(q_embedding, chunk_embedding) / (np.linalg.norm(q_embedding) * np.linalg.norm(chunk_embedding))
                similarities.append((similarity, chunk))
        
        similarities.sort(key=lambda x: x[0], reverse=True)
        
        results = []
        for sim, chunk in similarities[:top_k]:
            document = mongo.db.documents.find_one({'_id': chunk['document_id']})
            if document:
                results.append({
                    'document_id': str(document['_id']),
                    'title': document.get('title', 'N/A'),
                    'content': chunk['content'],
                    'page_number': chunk.get('page_number'),
                    'similarity': sim
                })
        return results
        """Query documents based on similarity to the query text"""
        if not self.embeddings_available:
            return []

        query_embedding = self.embedding_model.encode([query_text])[0].tolist()

        # Retrieve relevant document chunks using MongoDB's aggregation framework
        # This is a simplified approach. For true vector search, a dedicated vector DB or
        # MongoDB Atlas Vector Search would be used.
        relevant_chunks = DocumentChunk.find_by_embedding(query_embedding, top_k)

        results = []
        for chunk in relevant_chunks:
            document = Document.find_by_id(chunk['document_id'])
            if document:
                results.append({
                    'document_id': str(document['_id']),
                    'document_title': document['title'],
                    'chunk_content': chunk['content'],
                    'page_number': chunk['page_number'],
                    'similarity_score': chunk.get('similarity_score', 0.0)  # Placeholder
                })
        return results
        
        try:
            document.update_document(status='processing')

            # Extract text and pages info
            text_content, pages_info = self.extract_text_from_pdf(document.file_path)

            # Chunk text
            chunks_data = self.chunk_text(text_content, pages_info)

            # Generate embeddings for chunks
            chunk_contents = [chunk['content'] for chunk in chunks_data]
            embeddings = self.generate_embeddings(chunk_contents)

            # Create DocumentChunk records
            for i, chunk_data in enumerate(chunks_data):
                DocumentChunk.create(
                    document_id=str(document['_id']),
                    chunk_index=chunk_data['index'],
                    content=chunk_data['content'],
                    embedding=embeddings[i],
                    start_char=chunk_data['start_char'],
                    end_char=chunk_data['end_char'],
                    page_number=chunk_data['page_number']
                )
            document.update_document(status='processed')
            return True
            
        except Exception as e:
            print(f"Error processing document {document_id}: {e}")
            return False
    
    def search_documents(self, query: str, category: str = None, limit: int = 5) -> List[Dict]:
        """Search documents using semantic similarity"""
        if not query.strip():
            return []
        
        # Get query embedding
        query_embedding = None
        if self.embedding_model:
            try:
                query_embedding = self.embedding_model.encode([query])[0].tolist()
            except Exception:
                pass
        
        # Build base query
        chunks_query = DocumentChunk.query.join(Document)
        
        if category:
            chunks_query = chunks_query.filter(Document.category == category)
        
        chunks_query = chunks_query.filter(Document.is_active == True)
        
        # If we have embeddings, use semantic search
        if query_embedding and EMBEDDINGS_AVAILABLE:
            # Get all chunks with embeddings
            chunks = chunks_query.filter(DocumentChunk.embedding.isnot(None)).all()
            
            if chunks:
                # Calculate similarities
                similarities = []
                for chunk in chunks:
                    if chunk.embedding:
                        try:
                            chunk_embedding = np.array(chunk.embedding)
                            query_vec = np.array(query_embedding)
                            similarity = np.dot(chunk_embedding, query_vec) / (
                                np.linalg.norm(chunk_embedding) * np.linalg.norm(query_vec)
                            )
                            similarities.append((chunk, similarity))
                        except Exception:
                            similarities.append((chunk, 0))
                
                # Sort by similarity and return top results
                similarities.sort(key=lambda x: x[1], reverse=True)
                results = []
                
                for chunk, score in similarities[:limit]:
                    results.append({
                        'chunk': chunk.to_dict(),
                        'document': chunk.document.to_dict(),
                        'similarity_score': float(score),
                        'content': chunk.content
                    })
                
                return results
        
        # Fallback to text search
        chunks = chunks_query.filter(
            DocumentChunk.content.contains(query)
        ).limit(limit).all()
        
        results = []
        for chunk in chunks:
            results.append({
                'chunk': chunk.to_dict(),
                'document': chunk.document.to_dict(),
                'similarity_score': 0.5,  # Default score for text search
                'content': chunk.content
            })
        
        return results
    
    def get_document_content(self, document_id: str) -> Optional[str]:
        """Get full content of a document"""
        document = Document.query.get(document_id)
        return document.content_text if document else None
    
    def delete_document(self, document_id: str) -> bool:
        """Delete a document and its chunks"""
        document = Document.query.get(document_id)
        if not document:
            return False
        
        try:
            # Delete file
            if os.path.exists(document.file_path):
                os.remove(document.file_path)
            
            # Delete from database (chunks will be deleted due to cascade)
            db.session.delete(document)
            db.session.commit()
            return True
        except Exception:
            return False
