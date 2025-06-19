// Cập nhật tên file khi chọn
document.getElementById('file')?.addEventListener('change', function(e) {
    const fileName = e.target.files[0]?.name || 'Kéo thả hoặc click để chọn file';
    document.getElementById('fileLabel').textContent = fileName;
});

document.getElementById('verifyFile')?.addEventListener('change', function(e) {
    const fileName = e.target.files[0]?.name || 'Kéo thả hoặc click để chọn file';
    document.getElementById('verifyFileLabel').textContent = fileName;
});

// Xử lý ký số
document.getElementById('uploadForm')?.addEventListener('submit', async (e) => {
    e.preventDefault();
    const loading = document.getElementById('uploadLoading');
    const result = document.getElementById('signatureResult');
    
    loading.style.display = 'block';
    result.style.display = 'none';

    const formData = new FormData();
    const file = document.getElementById('file').files[0];
    formData.append('file', file);

    try {
        const response = await fetch('/upload', {
            method: 'POST',
            body: formData
        });
        const data = await response.json();
        
        document.getElementById('signature').textContent = data.signature;
        result.style.display = 'block';
        
        // Thêm vào lịch sử
        addToHistory('Ký số', file.name, data.signature);
    } catch (error) {
        showAlert('Lỗi khi ký số file: ' + error.message, 'danger');
    } finally {
        loading.style.display = 'none';
    }
});

// Xử lý xác thực
document.getElementById('verifyForm')?.addEventListener('submit', async (e) => {
    e.preventDefault();
    const loading = document.getElementById('verifyLoading');
    const result = document.getElementById('verifyResult');
    
    loading.style.display = 'block';
    result.style.display = 'none';

    const formData = new FormData();
    const file = document.getElementById('verifyFile').files[0];
    const signature = document.getElementById('signatureInput').value;
    
    formData.append('file', file);
    formData.append('signature', signature);

    try {
        const response = await fetch('/verify', {
            method: 'POST',
            body: formData
        });
        const data = await response.json();
        
        const alertDiv = result.querySelector('.alert');
        
        if (data.valid) {
            alertDiv.className = 'alert alert-success';
            alertDiv.innerHTML = '<i class="fas fa-check-circle"></i> Chữ ký hợp lệ!';
            addToHistory('Xác thực', file.name, signature, true);
        } else {
            alertDiv.className = 'alert alert-danger';
            alertDiv.innerHTML = '<i class="fas fa-times-circle"></i> Chữ ký không hợp lệ!';
            addToHistory('Xác thực', file.name, signature, false);
        }
        result.style.display = 'block';
    } catch (error) {
        showAlert('Lỗi khi xác thực: ' + error.message, 'danger');
    } finally {
        loading.style.display = 'none';
    }
});

// Chức năng sao chép chữ ký
function copySignature() {
    const signature = document.getElementById('signature').textContent;
    navigator.clipboard.writeText(signature).then(() => {
        showAlert('Đã sao chép chữ ký vào clipboard!', 'success');
    }).catch(err => {
        showAlert('Không thể sao chép chữ ký: ' + err, 'danger');
    });
}

// Hiển thị thông báo
function showAlert(message, type = 'info') {
    const alertDiv = document.createElement('div');
    alertDiv.className = `alert alert-${type} alert-dismissible fade show`;
    alertDiv.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
    `;
    
    const container = document.querySelector('.container');
    container.insertBefore(alertDiv, container.firstChild);
    
    setTimeout(() => {
        alertDiv.remove();
    }, 5000);
}

// Thêm vào lịch sử
function addToHistory(action, filename, signature, isValid = null) {
    const historyTable = document.getElementById('historyTable');
    if (!historyTable) return;

    const tbody = historyTable.querySelector('tbody');
    const row = document.createElement('tr');
    
    const date = new Date().toLocaleString();
    const status = isValid === null ? '' : 
                  isValid ? '<span class="text-success">Hợp lệ</span>' : 
                  '<span class="text-danger">Không hợp lệ</span>';
    
    row.innerHTML = `
        <td>${date}</td>
        <td>${action}</td>
        <td>${filename}</td>
        <td>${signature.substring(0, 20)}...</td>
        <td>${status}</td>
    `;
    
    tbody.insertBefore(row, tbody.firstChild);
}

// Xử lý kéo thả file
function setupDragAndDrop() {
    const dropZones = document.querySelectorAll('.custom-file-label');
    
    dropZones.forEach(zone => {
        zone.addEventListener('dragover', (e) => {
            e.preventDefault();
            zone.style.borderColor = 'var(--primary-color)';
            zone.style.background = '#e9ecef';
        });
        
        zone.addEventListener('dragleave', (e) => {
            e.preventDefault();
            zone.style.borderColor = '#dee2e6';
            zone.style.background = '#f8f9fa';
        });
        
        zone.addEventListener('drop', (e) => {
            e.preventDefault();
            zone.style.borderColor = '#dee2e6';
            zone.style.background = '#f8f9fa';
            
            const file = e.dataTransfer.files[0];
            if (file) {
                const input = zone.previousElementSibling;
                input.files = e.dataTransfer.files;
                zone.textContent = file.name;
            }
        });
    });
}

// Khởi tạo
document.addEventListener('DOMContentLoaded', () => {
    setupDragAndDrop();
});