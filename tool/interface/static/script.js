// Global variables to track current state
let currentToolType = '';
let currentSubType = '';

// Language options for dropdowns - will be populated from the HTML
let languages = [];

// Show main menu and hide all other sections
function showMainMenu() {
    hideAllSections();
    document.getElementById('main-menu').style.display = 'block';
    currentToolType = '';
    currentSubType = '';
}

// Show sub menu for the selected tool type
function showSubMenu(toolType) {
    hideAllSections();
    document.getElementById(toolType + '-menu').style.display = 'block';
    currentToolType = toolType;
    currentSubType = '';
}

// Show settings form for the selected tool sub type
function showSettings(toolType, subType) {
    hideAllSections();
    document.getElementById(subType + '-settings').style.display = 'block';
    currentToolType = toolType;
    currentSubType = subType;
}

// Hide all sections
function hideAllSections() {
    // Hide main menu
    document.getElementById('main-menu').style.display = 'none';
    
    // Hide sub menus
    const subMenus = document.querySelectorAll('.sub-menu');
    subMenus.forEach(menu => menu.style.display = 'none');
    
    // Hide settings
    const settings = document.querySelectorAll('.settings');
    settings.forEach(setting => setting.style.display = 'none');
    
    // Hide status message
    document.getElementById('status-message').style.display = 'none';
}

// Add a new language selector
function addLanguageSelector(containerId) {
    const container = document.getElementById(containerId);
    
    // Get languages from the first select element in the form
    const firstSelect = container.querySelector('select');
    const options = Array.from(firstSelect.options).map(option => 
        `<option value="${option.value}">${option.text}</option>`
    ).join('');
    
    const newSelector = document.createElement('div');
    newSelector.className = 'language-selector';
    
    newSelector.innerHTML = `
        <select name="target_languages[]" required>
            ${options}
        </select>
        <button type="button" class="remove-btn" onclick="removeLanguageSelector(this)">-</button>
    `;
    
    container.appendChild(newSelector);
}

// Remove a language selector
function removeLanguageSelector(button) {
    const container = button.parentElement.parentElement;
    if (container.children.length > 1) {
        button.parentElement.remove();
    }
}

// Handle form submissions
document.addEventListener('DOMContentLoaded', function() {
    // Add event listeners to all forms
    const forms = document.querySelectorAll('form');
    forms.forEach(form => {
        form.addEventListener('submit', function(e) {
            e.preventDefault();
            handleFormSubmit(form);
        });
    });
});

// Handle form submission
function handleFormSubmit(form) {
    const formData = new FormData(form);
    const params = {};
    
    // Process form data
    for (let [key, value] of formData.entries()) {
        if (key.endsWith('[]')) {
            // Handle arrays (target languages)
            const arrayKey = key.replace('[]', '');
            if (!params[arrayKey]) {
                params[arrayKey] = [];
            }
            params[arrayKey].push(value);
        } else {
            params[key] = value;
        }
    }
    
    // Validate that all fields are filled
    const isEmpty = Object.values(params).some(value => {
        if (Array.isArray(value)) {
            return value.length === 0 || value.some(v => !v.trim());
        }
        return !value || !value.trim();
    });
    
    if (isEmpty) {
        alert('All fields are required!');
        return;
    }
    
    // Show status message
    showStatusMessage('Processing...');
    
    // Send request to server
    fetch('/execute', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            tool_type: currentToolType,
            tool_subtype: currentSubType,
            params: params
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            checkStatus();
        } else {
            showStatusMessage(data.message, true);
        }
    })
    .catch(error => {
        showStatusMessage('Error: ' + error.message, true);
    });
}

// Show status message
function showStatusMessage(message, isError = false) {
    hideAllSections();
    const statusDiv = document.getElementById('status-message');
    const statusText = document.getElementById('status-text');
    const closeBtn = document.getElementById('close-btn');
    
    statusText.textContent = message;
    statusDiv.style.display = 'block';
    
    if (isError) {
        statusDiv.style.backgroundColor = '#f8d7da';
        statusDiv.style.borderColor = '#dc3545';
        statusDiv.querySelector('h2').style.color = '#dc3545';
        closeBtn.style.display = 'inline-block';
    } else {
        statusDiv.style.backgroundColor = '#e9f7ef';
        statusDiv.style.borderColor = '#28a745';
        statusDiv.querySelector('h2').style.color = '#28a745';
        closeBtn.style.display = 'none';
    }
}

// Check process status
function checkStatus() {
    fetch('/status')
    .then(response => response.json())
    .then(data => {
        const statusText = document.getElementById('status-text');
        const closeBtn = document.getElementById('close-btn');
        
        statusText.textContent = data.message;
        
        if (!data.running) {
            // Process completed
            if (data.message.includes('successfully')) {
                statusText.textContent = 'The process is complete, you can close the window';
                closeBtn.style.display = 'inline-block';
            } else {
                // Error occurred
                showStatusMessage(data.message, true);
            }
        } else {
            // Still running, check again in 2 seconds
            setTimeout(checkStatus, 2000);
        }
    })
    .catch(error => {
        showStatusMessage('Error checking status: ' + error.message, true);
    });
}

// Close the window
function closeWindow() {
    fetch('/close')
    .then(() => {
        window.close();
        // If window.close() doesn't work (browser restrictions), show a message
        setTimeout(() => {
            alert('Please close this window manually.');
        }, 1000);
    })
    .catch(error => {
        console.error('Error closing server:', error);
        window.close();
    });
}

// Initialize the interface
document.addEventListener('DOMContentLoaded', function() {
    showMainMenu();
});
