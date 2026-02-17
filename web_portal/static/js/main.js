// App Crawler Web Portal JavaScript

const API_BASE = '/api';
let currentPathId = null;

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    loadPaths();
    setupEventListeners();
});

function setupEventListeners() {
    document.getElementById('refreshBtn').addEventListener('click', loadPaths);
    document.getElementById('closeDetailsBtn').addEventListener('click', closeDetails);
    document.getElementById('cancelEditBtn').addEventListener('click', () => {
        document.getElementById('editForm').style.display = 'none';
    });
    document.getElementById('saveBtn').addEventListener('click', savePathEdits);
}

async function loadPaths() {
    const container = document.getElementById('pathsContainer');
    container.innerHTML = '<div class="loading">Loading paths...</div>';
    
    try {
        const response = await fetch(`${API_BASE}/paths`);
        const paths = await response.json();
        
        if (paths.length === 0) {
            container.innerHTML = `
                <div class="empty-state">
                    <h3>No paths yet</h3>
                    <p>Start crawling to create your first path!</p>
                </div>
            `;
            return;
        }
        
        container.innerHTML = paths.map(path => createPathCard(path)).join('');
        
        // Add click listeners
        document.querySelectorAll('.path-card').forEach(card => {
            card.addEventListener('click', () => viewPath(card.dataset.pathId));
        });
        
    } catch (error) {
        container.innerHTML = `
            <div class="error-message">
                Error loading paths: ${error.message}
            </div>
        `;
    }
}

function createPathCard(path) {
    const date = new Date(path.created_at).toLocaleDateString();
    const platformClass = path.platform.toLowerCase();
    
    return `
        <div class="path-card" data-path-id="${path.path_id}">
            <h3>${escapeHtml(path.name)}</h3>
            <div class="path-meta">
                <span class="platform-badge ${platformClass}">${path.platform.toUpperCase()}</span>
                <span class="step-count">${path.step_count} steps</span>
            </div>
            <div class="path-meta">
                <strong>App:</strong> ${escapeHtml(path.app_package)}
            </div>
            <div class="path-meta">
                <strong>Created:</strong> ${date}
            </div>
            ${path.description ? `<div class="path-meta">${escapeHtml(path.description)}</div>` : ''}
        </div>
    `;
}

async function viewPath(pathId) {
    currentPathId = pathId;
    const detailsSection = document.getElementById('pathDetails');
    const infoContainer = document.getElementById('pathInfo');
    const stepsContainer = document.getElementById('stepsContainer');
    const interventionsContainer = document.getElementById('interventionsContainer');
    
    detailsSection.style.display = 'block';
    infoContainer.innerHTML = '<div class="loading">Loading path details...</div>';
    stepsContainer.innerHTML = '';
    interventionsContainer.innerHTML = '';
    
    try {
        const response = await fetch(`${API_BASE}/paths/${pathId}`);
        const data = await response.json();
        
        const path = data.path;
        const steps = data.steps;
        const interventions = data.interventions;
        
        // Display path info
        infoContainer.innerHTML = `
            <h3>${escapeHtml(path.name)}</h3>
            <div class="info-row">
                <span class="info-label">Path ID:</span>
                <span class="info-value">${escapeHtml(path.path_id)}</span>
            </div>
            <div class="info-row">
                <span class="info-label">Platform:</span>
                <span class="info-value">
                    <span class="platform-badge ${path.platform}">${path.platform.toUpperCase()}</span>
                </span>
            </div>
            <div class="info-row">
                <span class="info-label">App Package:</span>
                <span class="info-value">${escapeHtml(path.app_package)}</span>
            </div>
            <div class="info-row">
                <span class="info-label">Created:</span>
                <span class="info-value">${new Date(path.created_at).toLocaleString()}</span>
            </div>
            ${path.description ? `
            <div class="info-row">
                <span class="info-label">Description:</span>
                <span class="info-value">${escapeHtml(path.description)}</span>
            </div>
            ` : ''}
            <div style="margin-top: 20px;">
                <button class="btn btn-primary btn-small" onclick="editPath()">Edit</button>
                <button class="btn btn-danger btn-small" onclick="deletePath('${path.path_id}')">Delete</button>
            </div>
        `;
        
        // Display steps
        if (steps.length > 0) {
            stepsContainer.innerHTML = `
                <h3>Crawl Steps (${steps.length})</h3>
                ${steps.map(step => createStepItem(step)).join('')}
            `;
        }
        
        // Display interventions
        if (interventions.length > 0) {
            interventionsContainer.innerHTML = `
                <h3>Human Interventions (${interventions.length})</h3>
                ${interventions.map(intervention => createInterventionItem(intervention)).join('')}
            `;
        }
        
        // Scroll to details
        detailsSection.scrollIntoView({ behavior: 'smooth' });
        
    } catch (error) {
        infoContainer.innerHTML = `
            <div class="error-message">
                Error loading path details: ${error.message}
            </div>
        `;
    }
}

function createStepItem(step) {
    return `
        <div class="step-item">
            <div class="step-header">
                <span class="step-number">Step ${step.step_number}</span>
                <span class="action-badge">${step.action_type.toUpperCase()}</span>
            </div>
            <div class="step-details">
                <strong>Element:</strong> ${escapeHtml(step.element_selector || 'N/A')}<br>
                ${step.input_value ? `<strong>Input:</strong> ${escapeHtml(step.input_value)}<br>` : ''}
                ${step.element_attributes && step.element_attributes.text ? 
                    `<strong>Element Text:</strong> ${escapeHtml(step.element_attributes.text)}<br>` : ''}
            </div>
            ${step.ai_reasoning ? `
            <div class="ai-reasoning">
                <strong>🤖 AI Reasoning:</strong> ${escapeHtml(step.ai_reasoning)}
            </div>
            ` : ''}
            ${step.screenshot_path ? `
            <div class="step-screenshot">
                <img src="/screenshots/${step.screenshot_path.split('/').slice(-2).join('/')}" 
                     alt="Screenshot step ${step.step_number}"
                     onclick="window.open(this.src, '_blank')">
            </div>
            ` : ''}
        </div>
    `;
}

function createInterventionItem(intervention) {
    return `
        <div class="intervention-item">
            <div class="intervention-header">
                Step ${intervention.step_number} - ${escapeHtml(intervention.intervention_type)}
            </div>
            <div class="question">
                <strong>🤖 AI Question:</strong><br>
                ${escapeHtml(intervention.ai_question)}
            </div>
            <div class="response">
                <strong>👤 Human Response:</strong><br>
                ${escapeHtml(intervention.human_response)}
            </div>
            <div style="margin-top: 10px; color: #666; font-size: 0.9em;">
                ${new Date(intervention.created_at).toLocaleString()}
            </div>
        </div>
    `;
}

function editPath() {
    const editForm = document.getElementById('editForm');
    const nameInput = document.getElementById('editName');
    const descInput = document.getElementById('editDescription');
    
    // Get current values
    fetch(`${API_BASE}/paths/${currentPathId}`)
        .then(res => res.json())
        .then(data => {
            nameInput.value = data.path.name;
            descInput.value = data.path.description || '';
            editForm.style.display = 'block';
            editForm.scrollIntoView({ behavior: 'smooth' });
        });
}

async function savePathEdits() {
    const name = document.getElementById('editName').value;
    const description = document.getElementById('editDescription').value;
    
    try {
        const response = await fetch(`${API_BASE}/paths/${currentPathId}`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ name, description })
        });
        
        if (response.ok) {
            document.getElementById('editForm').style.display = 'none';
            viewPath(currentPathId);
            loadPaths();
        } else {
            alert('Error updating path');
        }
    } catch (error) {
        alert('Error updating path: ' + error.message);
    }
}

async function deletePath(pathId) {
    if (!confirm('Are you sure you want to delete this path? This cannot be undone.')) {
        return;
    }
    
    try {
        const response = await fetch(`${API_BASE}/paths/${pathId}`, {
            method: 'DELETE'
        });
        
        if (response.ok) {
            closeDetails();
            loadPaths();
        } else {
            alert('Error deleting path');
        }
    } catch (error) {
        alert('Error deleting path: ' + error.message);
    }
}

function closeDetails() {
    document.getElementById('pathDetails').style.display = 'none';
    currentPathId = null;
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}
