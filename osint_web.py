#!/usr/bin/env python3
"""
OSINT Web Interface
Flask-based web application for comprehensive OSINT investigations
"""

from flask import Flask, render_template, request, jsonify, send_file, redirect, url_for
from flask_cors import CORS
import json
import os
import threading
import time
from datetime import datetime
from comprehensive_osint_api import ComprehensiveOSINTEngine, OSINTResult
from typing import List, Dict, Any
import io

app = Flask(__name__)
CORS(app)

# Global variables
engine = ComprehensiveOSINTEngine()
active_searches = {}
search_history = []

@app.route('/')
def index():
    """Main dashboard"""
    return '''<!DOCTYPE html>
<html>
<head>
    <title>OSINT Search Engine</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; background: #f5f5f5; }
        .container { max-width: 800px; margin: 0 auto; background: white; padding: 20px; border-radius: 8px; }
        .form-group { margin: 15px 0; }
        .form-control { width: 100%; padding: 8px; border: 1px solid #ddd; border-radius: 4px; }
        .btn { padding: 10px 20px; border: none; border-radius: 4px; cursor: pointer; margin: 5px; }
        .btn-primary { background: #007bff; color: white; }
        .btn-secondary { background: #6c757d; color: white; }
        .result-card { background: #f8f9fa; padding: 15px; margin: 10px 0; border-radius: 4px; border-left: 4px solid #28a745; }
        .result-failed { border-left-color: #dc3545; }
        .progress { width: 100%; height: 20px; background: #e9ecef; border-radius: 10px; overflow: hidden; }
        .progress-bar { height: 100%; background: #007bff; transition: width 0.3s; }
    </style>
</head>
<body>
    <div class="container">
        <h1>🔍 OSINT Search Engine</h1>
        <p>Comprehensive Open Source Intelligence Framework</p>
        
        <form id="searchForm" onsubmit="startSearch(event)">
            <div class="form-group">
                <label>Search Query:</label>
                <input type="text" id="query" class="form-control" placeholder="Enter username, URL, image URL..." required>
            </div>
            
            <div class="form-group">
                <label>Search Types:</label><br>
                <label><input type="checkbox" value="social_username"> Social Media Username</label><br>
                <label><input type="checkbox" value="bulk_username"> Bulk Username Check</label><br>
                <label><input type="checkbox" value="image_analysis"> Image Analysis</label><br>
                <label><input type="checkbox" value="utility_url_expansion"> URL Expansion</label><br>
                <label><input type="checkbox" value="utility_pokemon_go_trainer_code"> Pokemon Go</label>
            </div>
            
            <button type="submit" class="btn btn-primary">🔍 Start Search</button>
            <button type="button" class="btn btn-secondary" onclick="autoDetect()">🎯 Auto-Detect</button>
        </form>
        
        <div id="progress" style="display: none;">
            <h3>Search Progress</h3>
            <div class="progress">
                <div id="progressBar" class="progress-bar" style="width: 0%"></div>
            </div>
            <p id="status">Starting search...</p>
        </div>
        
        <div id="results" style="display: none;">
            <h3>Search Results</h3>
            <div id="summary"></div>
            <div id="resultsList"></div>
            <button onclick="downloadResults('json')" class="btn btn-secondary">📄 Download JSON</button>
            <button onclick="downloadResults('csv')" class="btn btn-secondary">📊 Download CSV</button>
        </div>
    </div>

    <script>
        let currentSearchId = null;
        
        function startSearch(event) {
            event.preventDefault();
            
            const query = document.getElementById('query').value.trim();
            const searchTypes = Array.from(document.querySelectorAll('input[type="checkbox"]:checked')).map(cb => cb.value);
            
            if (!query) {
                alert('Please enter a search query');
                return;
            }
            
            if (searchTypes.length === 0) {
                alert('Please select at least one search type');
                return;
            }
            
            document.getElementById('progress').style.display = 'block';
            document.getElementById('results').style.display = 'none';
            
            fetch('/search', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ query: query, search_types: searchTypes })
            })
            .then(response => response.json())
            .then(data => {
                currentSearchId = data.search_id;
                monitorSearch();
            })
            .catch(error => {
                alert('Error: ' + error);
            });
        }
        
        function monitorSearch() {
            const interval = setInterval(() => {
                fetch(`/search/${currentSearchId}/status`)
                .then(response => response.json())
                .then(data => {
                    document.getElementById('progressBar').style.width = (data.progress || 50) + '%';
                    document.getElementById('status').textContent = data.status;
                    
                    if (data.status === 'completed') {
                        clearInterval(interval);
                        showResults(data);
                    } else if (data.status === 'failed') {
                        clearInterval(interval);
                        alert('Search failed: ' + (data.error || 'Unknown error'));
                    }
                });
            }, 1000);
        }
        
        function showResults(data) {
            document.getElementById('progress').style.display = 'none';
            document.getElementById('results').style.display = 'block';
            
            const successful = data.results.filter(r => r.success).length;
            document.getElementById('summary').innerHTML = 
                `<p><strong>Results:</strong> ${successful}/${data.results.length} successful searches</p>`;
            
            let resultsHtml = '';
            data.results.forEach(result => {
                const cardClass = result.success ? 'result-card' : 'result-card result-failed';
                resultsHtml += `
                    <div class="${cardClass}">
                        <h4>${result.service} - ${result.query_type}</h4>
                        <p><strong>Query:</strong> ${result.query}</p>
                        <p><strong>Success:</strong> ${result.success ? '✅ Yes' : '❌ No'}</p>
                        <p><strong>Response Time:</strong> ${result.response_time.toFixed(2)}s</p>
                        ${result.data ? `<details><summary>Data</summary><pre>${JSON.stringify(result.data, null, 2)}</pre></details>` : ''}
                        ${result.error ? `<p style="color: red;"><strong>Error:</strong> ${result.error}</p>` : ''}
                    </div>
                `;
            });
            document.getElementById('resultsList').innerHTML = resultsHtml;
        }
        
        function autoDetect() {
            const query = document.getElementById('query').value.trim();
            document.querySelectorAll('input[type="checkbox"]').forEach(cb => cb.checked = false);
            
            if (query.includes('http') && (query.includes('bit.ly') || query.includes('tinyurl'))) {
                document.querySelector('input[value="utility_url_expansion"]').checked = true;
            } else if (query.includes('http') && query.match(/\\.(jpg|png|gif)$/i)) {
                document.querySelector('input[value="image_analysis"]').checked = true;
            } else if (query.match(/^\\d{12}$/)) {
                document.querySelector('input[value="utility_pokemon_go_trainer_code"]').checked = true;
            } else {
                document.querySelector('input[value="social_username"]').checked = true;
                document.querySelector('input[value="bulk_username"]').checked = true;
            }
        }
        
        function downloadResults(format) {
            if (currentSearchId) {
                window.open(`/search/${currentSearchId}/download/${format}`);
            }
        }
    </script>
</body>
</html>'''

@app.route('/search', methods=['POST'])
def search():
    """Initiate OSINT search"""
    data = request.get_json()
    query = data.get('query', '').strip()
    search_types = data.get('search_types', [])
    search_id = f"search_{int(time.time() * 1000)}"
    
    if not query:
        return jsonify({'error': 'Query is required'}), 400
    
    if not search_types:
        search_types = engine._determine_search_types(query)
    
    active_searches[search_id] = {
        'status': 'running',
        'query': query,
        'search_types': search_types,
        'results': [],
        'progress': 0,
        'start_time': datetime.now().isoformat()
    }
    
    thread = threading.Thread(target=perform_search, args=(search_id, query, search_types))
    thread.daemon = True
    thread.start()
    
    return jsonify({'search_id': search_id, 'status': 'started'})

def perform_search(search_id: str, query: str, search_types: List[str]):
    """Perform OSINT search in background"""
    try:
        results = engine.search_comprehensive(query, search_types)
        active_searches[search_id]['results'] = [result.__dict__ for result in results]
        active_searches[search_id]['status'] = 'completed'
        active_searches[search_id]['progress'] = 100
    except Exception as e:
        active_searches[search_id]['status'] = 'failed'
        active_searches[search_id]['error'] = str(e)

@app.route('/search/<search_id>/status')
def search_status(search_id):
    """Get search status"""
    if search_id not in active_searches:
        return jsonify({'error': 'Search not found'}), 404
    return jsonify(active_searches[search_id])

@app.route('/search/<search_id>/download/<format>')
def download_results(search_id, format):
    """Download results"""
    if search_id not in active_searches:
        return jsonify({'error': 'Search not found'}), 404
    
    search_data = active_searches[search_id]
    if search_data['status'] != 'completed':
        return jsonify({'error': 'Search not completed'}), 400
    
    results = [OSINTResult(**result_dict) for result_dict in search_data['results']]
    
    if format == 'json':
        report = engine.generate_comprehensive_report(results, 'json')
        return send_file(
            io.BytesIO(report.encode()),
            mimetype='application/json',
            as_attachment=True,
            download_name=f"osint_results_{search_id}.json"
        )
    elif format == 'csv':
        report = engine.generate_comprehensive_report(results, 'csv')
        return send_file(
            io.BytesIO(report.encode()),
            mimetype='text/csv',
            as_attachment=True,
            download_name=f"osint_results_{search_id}.csv"
        )
    
    return jsonify({'error': 'Unsupported format'}), 400

if __name__ == '__main__':
    print("🌐 Starting OSINT Web Interface...")
    print("📱 Access at: http://localhost:5000")
    app.run(debug=True, host='0.0.0.0', port=5000)
