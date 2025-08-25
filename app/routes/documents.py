"""
Document management routes for admin interface
"""

from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for
from werkzeug.utils import secure_filename
from app.models.mongo_models import Document, DocumentChunk, GuestRequest
from app.services.document_service import DocumentService
import os

documents_bp = Blueprint('documents', __name__)
document_service = DocumentService()

@documents_bp.route('/admin/documents')
def admin_documents():
    """Admin document management interface"""
    documents = list(mongo.db.documents.find({'is_active': True}).sort('upload_date', -1))
    return render_template('admin/documents.html', documents=documents)

@documents_bp.route('/admin/documents/upload', methods=['GET', 'POST'])
def upload_document():
    """Upload new document"""
    if request.method == 'POST':
        try:
            if 'file' not in request.files:
                flash('No file selected', 'error')
                return redirect(request.url)
            
            file = request.files['file']
            if file.filename == '':
                flash('No file selected', 'error')
                return redirect(request.url)
            
            if file and document_service.allowed_file(file.filename):
                category = request.form.get('category', 'policy')
                title = request.form.get('title', '')
                description = request.form.get('description', '')
                uploaded_by = request.form.get('uploaded_by', 'admin')
                
                document_id = document_service.upload_document(
                    file=file,
                    category=category,
                    title=title,
                    description=description,
                    uploaded_by=uploaded_by
                )
                
                # Retrieve the document to get its title for the flash message
                document = mongo.db.documents.find_one({'_id': document_id})
                if document:
                    flash(f"Document \"{document.get('title', 'Unknown')}\" uploaded successfully!", 'success')
                else:
                    flash('Document uploaded, but could not retrieve details.', 'warning')
                return redirect(url_for('documents.admin_documents'))
            else:
                flash('Invalid file type. Please upload PDF, TXT, DOC, or DOCX files.', 'error')
        
        except Exception as e:
            flash(f'Error uploading document: {str(e)}', 'error')
    
    return render_template('admin/upload_document.html')

@documents_bp.route('/admin/documents/<document_id>')
def view_document(document_id):
    """View document details and chunks"""
    document = mongo.db.documents.find_one({'_id': document_id})
    if not document:
        flash('Document not found', 'error')
        return redirect(url_for('documents.admin_documents'))
    chunks = list(mongo.db.document_chunks.find({'document_id': document_id}).sort('chunk_index', 1))
    return render_template('admin/document_detail.html', document=document, chunks=chunks)

@documents_bp.route('/admin/documents/<document_id>/delete', methods=['POST'])
def delete_document(document_id):
    """Delete document"""
    try:
        success = document_service.delete_document(document_id)
        if success:
            flash('Document deleted successfully!', 'success')
        else:
            flash('Error deleting document', 'error')
    except Exception as e:
        flash(f'Error deleting document: {str(e)}', 'error')
    
    return redirect(url_for('documents.admin_documents'))

@documents_bp.route('/admin/documents/<document_id>/reprocess', methods=['POST'])
def reprocess_document(document_id):
    """Reprocess document for indexing"""
    try:
        success = document_service.process_document(document_id)
        if success:
            flash('Document reprocessed successfully!', 'success')
        else:
            flash('Error reprocessing document', 'error')
    except Exception as e:
        flash(f'Error reprocessing document: {str(e)}', 'error')
    
    return redirect(url_for('documents.view_document', document_id=document_id))

@documents_bp.route('/api/documents/search')
def search_documents():
    """API endpoint for document search"""
    query = request.args.get('q', '')
    category = request.args.get('category', '')
    limit = int(request.args.get('limit', 5))
    
    if not query:
        return jsonify({'results': []})
    
    try:
        results = document_service.search_documents(
            query=query,
            category=category if category else None,
            limit=limit
        )
        
        return jsonify({
            'results': results,
            'query': query,
            'total': len(results)
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@documents_bp.route('/admin/requests')
def admin_requests():
    """Admin interface for guest requests"""
    status_filter = request.args.get('status', 'all')
    priority_filter = request.args.get('priority', 'all')
    
    filters = {}
    if status_filter != 'all':
        filters['status'] = status_filter
    
    if priority_filter != 'all':
        filters['priority'] = priority_filter
    
    requests = list(mongo.db.guest_requests.find(filters).sort('created_at', -1))
    
    return render_template('admin/requests.html', 
                         requests=requests,
                         status_filter=status_filter,
                         priority_filter=priority_filter)

@documents_bp.route('/admin/requests/<request_id>/update', methods=['POST'])
def update_request(request_id):
    """Update guest request status"""
    guest_request = mongo.db.guest_requests.find_one({'_id': request_id})
    if not guest_request:
        flash('Guest request not found', 'error')
        return redirect(url_for('documents.admin_requests'))
    
    try:
        update_fields = {}
        status = request.form.get('status', guest_request.get('status'))
        priority = request.form.get('priority', guest_request.get('priority'))
        assigned_to = request.form.get('assigned_to', guest_request.get('assigned_to'))
        notes = request.form.get('notes', guest_request.get('notes'))

        if status: update_fields['status'] = status
        if priority: update_fields['priority'] = priority
        if assigned_to: update_fields['assigned_to'] = assigned_to
        if notes: update_fields['notes'] = notes
        
        if status == 'completed' and not guest_request.get('completed_time'):
            update_fields['completed_time'] = datetime.utcnow()
        
        if update_fields:
            mongo.db.guest_requests.update_one({'_id': guest_request['_id']}, {'$set': update_fields})
        
        flash('Request updated successfully!', 'success')
    
    except Exception as e:
        flash(f'Error updating request: {str(e)}', 'error')
    
    return redirect(url_for('documents.admin_requests'))

@documents_bp.route('/api/requests/<request_id>/status', methods=['PUT'])
def update_request_status(request_id):
    """API endpoint to update request status"""
    guest_request = mongo.db.guest_requests.find_one({'_id': request_id})
    if not guest_request:
        return jsonify({'error': 'Guest request not found'}), 404
    
    try:
        data = request.get_json()
        update_fields = {}
        
        if 'status' in data: update_fields['status'] = data['status']
        if 'assigned_to' in data: update_fields['assigned_to'] = data['assigned_to']
        if 'notes' in data: update_fields['notes'] = data['notes']
        
        if update_fields.get('status') == 'completed' and not guest_request.get('completed_time'):
            update_fields['completed_time'] = datetime.utcnow()
        
        if update_fields:
            mongo.db.guest_requests.update_one({'_id': request_id}, {'$set': update_fields})
        
        updated_request = mongo.db.guest_requests.find_one({'_id': request_id})
        return jsonify({
            'success': True,
            'request': updated_request
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500
