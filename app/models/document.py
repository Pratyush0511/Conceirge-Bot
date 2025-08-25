"""
Document model for storing hotel policy PDFs and other documents
"""

from datetime import datetime
import uuid

class Document:
    def __init__(self, filename, original_filename, file_path, file_size=None, mime_type=None, category=None, title=None, description=None, content_text=None, is_indexed=False, is_active=True, upload_date=None, last_updated=None, uploaded_by=None, id=None):
        self._id = id if id else str(uuid.uuid4())
        self.filename = filename
        self.original_filename = original_filename
        self.file_path = file_path
        self.file_size = file_size
        self.mime_type = mime_type
        self.category = category
        self.title = title
        self.description = description
        self.content_text = content_text
        self.is_indexed = is_indexed
        self.is_active = is_active
        self.upload_date = upload_date if upload_date else datetime.utcnow()
        self.last_updated = last_updated if last_updated else datetime.utcnow()
        self.uploaded_by = uploaded_by

    def to_dict(self):
        return {
            '_id': self._id,
            'filename': self.filename,
            'original_filename': self.original_filename,
            'file_path': self.file_path,
            'file_size': self.file_size,
            'mime_type': self.mime_type,
            'category': self.category,
            'title': self.title,
            'description': self.description,
            'content_text': self.content_text,
            'is_indexed': self.is_indexed,
            'is_active': self.is_active,
            'upload_date': self.upload_date.isoformat(),
            'last_updated': self.last_updated.isoformat(),
            'uploaded_by': self.uploaded_by
        }

    @staticmethod
    def from_dict(data):
        return Document(
            id=data.get('_id'),
            filename=data['filename'],
            original_filename=data['original_filename'],
            file_path=data['file_path'],
            file_size=data.get('file_size'),
            mime_type=data.get('mime_type'),
            category=data.get('category'),
            title=data.get('title'),
            description=data.get('description'),
            content_text=data.get('content_text'),
            is_indexed=data.get('is_indexed', False),
            is_active=data.get('is_active', True),
            upload_date=datetime.fromisoformat(data['upload_date']) if 'upload_date' in data and isinstance(data['upload_date'], str) else data.get('upload_date'),
            last_updated=datetime.fromisoformat(data['last_updated']) if 'last_updated' in data and isinstance(data['last_updated'], str) else data.get('last_updated'),
            uploaded_by=data.get('uploaded_by')
        )

class DocumentChunk:
    def __init__(self, document_id, chunk_index, content, page_number=None, start_char=None, end_char=None, embedding=None, created_at=None, id=None):
        self._id = id if id else str(uuid.uuid4())
        self.document_id = document_id
        self.chunk_index = chunk_index
        self.content = content
        self.page_number = page_number
        self.start_char = start_char
        self.end_char = end_char
        self.embedding = embedding
        self.created_at = created_at if created_at else datetime.utcnow()

    def to_dict(self):
        return {
            '_id': self._id,
            'document_id': self.document_id,
            'chunk_index': self.chunk_index,
            'content': self.content,
            'page_number': self.page_number,
            'start_char': self.start_char,
            'end_char': self.end_char,
            'embedding': self.embedding,
            'created_at': self.created_at.isoformat()
        }

    @staticmethod
    def from_dict(data):
        return DocumentChunk(
            id=data.get('_id'),
            document_id=data['document_id'],
            chunk_index=data['chunk_index'],
            content=data['content'],
            page_number=data.get('page_number'),
            start_char=data.get('start_char'),
            end_char=data.get('end_char'),
            embedding=data.get('embedding'),
            created_at=datetime.fromisoformat(data['created_at']) if 'created_at' in data and isinstance(data['created_at'], str) else data.get('created_at')
        )

class GuestRequest:
    def __init__(self, conversation_id, user_id, request_type, title, description, priority='medium', status='no', room_number=None, requested_time=None, completed_time=None, assigned_to=None, notes=None, guest_rating=None, guest_feedback=None, created_at=None, updated_at=None, id=None):
        self._id = id if id else str(uuid.uuid4())
        self.conversation_id = conversation_id
        self.user_id = user_id
        self.request_type = request_type
        self.title = title
        self.description = description
        self.priority = priority
        self.status = status
        self.room_number = room_number
        self.requested_time = requested_time
        self.completed_time = completed_time
        self.assigned_to = assigned_to
        self.notes = notes
        self.guest_rating = guest_rating
        self.guest_feedback = guest_feedback
        self.created_at = created_at if created_at else datetime.utcnow()
        self.updated_at = updated_at if updated_at else datetime.utcnow()

    def to_dict(self):
        return {
            '_id': self._id,
            'conversation_id': self.conversation_id,
            'user_id': self.user_id,
            'request_type': self.request_type,
            'title': self.title,
            'description': self.description,
            'priority': self.priority,
            'status': self.status,
            'room_number': self.room_number,
            'requested_time': self.requested_time.isoformat() if self.requested_time else None,
            'completed_time': self.completed_time.isoformat() if self.completed_time else None,
            'assigned_to': self.assigned_to,
            'notes': self.notes,
            'guest_rating': self.guest_rating,
            'guest_feedback': self.guest_feedback,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }

    @staticmethod
    def from_dict(data):
        return GuestRequest(
            id=data.get('_id'),
            conversation_id=data['conversation_id'],
            user_id=data['user_id'],
            request_type=data['request_type'],
            title=data['title'],
            description=data['description'],
            priority=data.get('priority'),
            status=data.get('status'),
            room_number=data.get('room_number'),
            requested_time=datetime.fromisoformat(data['requested_time']) if 'requested_time' in data and isinstance(data['requested_time'], str) else data.get('requested_time'),
            completed_time=datetime.fromisoformat(data['completed_time']) if 'completed_time' in data and isinstance(data['completed_time'], str) else data.get('completed_time'),
            assigned_to=data.get('assigned_to'),
            notes=data.get('notes'),
            guest_rating=data.get('guest_rating'),
            guest_feedback=data.get('guest_feedback'),
            created_at=datetime.fromisoformat(data['created_at']) if 'created_at' in data and isinstance(data['created_at'], str) else data.get('created_at'),
            updated_at=datetime.fromisoformat(data['updated_at']) if 'updated_at' in data and isinstance(data['updated_at'], str) else data.get('updated_at')
        )
