// 文件上传相关元素
const fileInput = document.getElementById('fileInput');
const resultCard = document.getElementById('resultCard');
const fileTypeEl = document.getElementById('fileType');
const kvResultEl = document.getElementById('kvResult');
const tableResultEl = document.getElementById('tableResult');
const previewCard = document.getElementById('previewCard');
const imagePreview = document.getElementById('imagePreview');
const pdfPreview = document.getElementById('pdfPreview');
const previewContainer = document.getElementById('previewContainer'); // 新增元素

// 配置管理相关元素
const configTable = document.getElementById('configTable');
const configForm = document.getElementById('configForm');
const saveConfigBtn = document.getElementById('saveConfigBtn');

// 调试函数
function debug(message, data = null) {
    const timestamp = new Date().toLocaleTimeString();
    if (data) {
        console.log(`[${timestamp}] ${message}:`, data);
    } else {
        console.log(`[${timestamp}] ${message}`);
    }
}

// 预览文件
async function previewFile(file) {
    debug('开始预览文件', { name: file.name, type: file.type });
    
    // 清除之前的预览
    imagePreview.classList.add('d-none');
    pdfPreview.classList.add('d-none');
    previewCard.classList.add('d-none');
    
    if (file.type.startsWith('image/')) {
        // 预览图片
        const reader = new FileReader();
        reader.onload = (e) => {
            imagePreview.src = e.target.result;
            imagePreview.classList.remove('d-none');
            previewCard.classList.remove('d-none');
        };
        reader.readAsDataURL(file);
    } else if (file.type === 'application/pdf') {
        try {
            // 显示加载状态
            pdfPreview.classList.remove('d-none');
            previewCard.classList.remove('d-none');
            
            const loadingContext = pdfPreview.getContext('2d');
            loadingContext.fillStyle = '#f8f9fa';
            loadingContext.fillRect(0, 0, pdfPreview.width, pdfPreview.height);
            loadingContext.fillStyle = '#6c757d';
            loadingContext.font = '16px Arial';
            loadingContext.textAlign = 'center';
            loadingContext.fillText('正在加载PDF...', pdfPreview.width / 2, pdfPreview.height / 2);

            // 配置PDF.js
            pdfjsLib.GlobalWorkerOptions.workerSrc = 'https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.11.174/pdf.worker.min.js';
            
            // 创建URL
            const url = URL.createObjectURL(file);
            
            try {
                const loadingTask = pdfjsLib.getDocument({
                    url: url,
                    cMapUrl: 'https://cdn.jsdelivr.net/npm/pdfjs-dist@3.11.174/cmaps/',
                    cMapPacked: true,
                    standardFontDataUrl: 'https://cdn.jsdelivr.net/npm/pdfjs-dist@3.11.174/standard_fonts/',
                    enableXfa: true,
                    useSystemFonts: true
                });

                const pdf = await loadingTask.promise;
                const page = await pdf.getPage(1);
                
                // 获取原始尺寸
                const originalViewport = page.getViewport({ scale: 1.0 });
                
                // 计算合适的缩放比例
                const containerWidth = previewContainer.clientWidth - 40;
                const containerHeight = previewContainer.clientHeight - 40;
                const widthScale = containerWidth / originalViewport.width;
                const heightScale = containerHeight / originalViewport.height;
                const scale = Math.min(widthScale, heightScale, 2.0);
                
                const viewport = page.getViewport({ scale: scale });
                
                // 设置canvas
                const canvas = pdfPreview;
                canvas.width = viewport.width;
                canvas.height = viewport.height;
                
                // 渲染PDF页面
                const renderContext = {
                    canvasContext: canvas.getContext('2d'),
                    viewport: viewport
                };
                
                await page.render(renderContext).promise;
                debug('PDF渲染完成');
                
            } catch (error) {
                console.error('Error rendering PDF:', error);
                debug('PDF渲染错误', error);
                
                const errorContext = pdfPreview.getContext('2d');
                errorContext.fillStyle = '#f8d7da';
                errorContext.fillRect(0, 0, pdfPreview.width, pdfPreview.height);
                errorContext.fillStyle = '#721c24';
                errorContext.font = '16px Arial';
                errorContext.textAlign = 'center';
                errorContext.fillText('PDF加载失败，请重试', pdfPreview.width / 2, pdfPreview.height / 2);
            } finally {
                URL.revokeObjectURL(url);
            }
        } catch (error) {
            console.error('Error in PDF preview:', error);
            debug('PDF预览错误', error);
        }
    }
}

// 文件选择处理
fileInput.addEventListener('change', async () => {
    const file = fileInput.files[0];
    if (!file) {
        return;
    }

    try {
        debug('开始处理文件', { name: file.name, size: file.size, type: file.type });
        fileInput.disabled = true;
        resultCard.classList.add('loading');

        // 预览文件
        await previewFile(file);

        // 上传文件到OSS并处理
        const formData = new FormData();
        formData.append('file', file);
        debug('开始上传文件');
        const response = await fetch('http://localhost:5000/api/upload', {
            method: 'POST',
            body: formData
        });
        
        if (!response.ok) {
            const error = await response.json();
            debug('上传失败', error);
            throw new Error(error.error || '上传失败');
        }
        
        const result = await response.json();
        debug('处理成功', result);

        // 显示结果
        displayResult(result);
    } catch (error) {
        console.error('Error:', error);
        alert(error.message || '上传或处理过程中出现错误');
    } finally {
        fileInput.disabled = false;
        resultCard.classList.remove('loading');
        fileInput.value = ''; // 清空文件输入，允许重新选择同一文件
    }
});

// 显示抽取结果
function displayResult(result) {
    try {
        debug('开始解析结果');
        const data = JSON.parse(result.data);
        if (!data) {
            throw new Error('返回数据格式错误');
        }
        debug('解析后的数据', data);
        
        // 显示文件类型
        fileTypeEl.textContent = data.file_type || '未知类型';
        debug('文件类型', data.file_type);

        // 显示键值对结果
        kvResultEl.innerHTML = '';
        if (data.kv_result && Object.keys(data.kv_result).length > 0) {
            debug('显示键值对结果', data.kv_result);
            Object.entries(data.kv_result).forEach(([key, value]) => {
                const col = document.createElement('div');
                col.className = 'col-md-6 col-lg-4';
                col.innerHTML = `
                    <div class="kv-item">
                        <strong>${key}：</strong>
                        <span>${value}</span>
                    </div>
                `;
                kvResultEl.appendChild(col);
            });
        } else {
            debug('没有键值对数据');
            kvResultEl.innerHTML = '<div class="alert alert-info">没有找到键值对数据</div>';
        }

        // 显示表格结果
        tableResultEl.innerHTML = '';
        if (data.table_result && data.table_result.length > 0) {
            debug('显示表格结果', data.table_result);
            const headers = Object.keys(data.table_result[0]);
            const table = document.createElement('table');
            table.className = 'table table-striped';
            
            // 表头
            const thead = document.createElement('thead');
            thead.innerHTML = `
                <tr>
                    ${headers.map(h => `<th>${h}</th>`).join('')}
                </tr>
            `;
            table.appendChild(thead);

            // 表格内容
            const tbody = document.createElement('tbody');
            data.table_result.forEach(row => {
                const tr = document.createElement('tr');
                tr.innerHTML = headers.map(h => `<td>${row[h] || ''}</td>`).join('');
                tbody.appendChild(tr);
            });
            table.appendChild(tbody);
            tableResultEl.appendChild(table);
        } else {
            debug('没有表格数据');
            tableResultEl.innerHTML = '<div class="alert alert-info">没有找到表格数据</div>';
        }

        resultCard.classList.remove('d-none');
    } catch (error) {
        console.error('Error parsing result:', error);
        debug('结果解析错误', error);
        alert('处理结果格式错误');
        resultCard.classList.add('d-none');
    }
}

// 加载配置列表
async function loadConfigs() {
    try {
        debug('开始加载配置列表');
        const response = await fetch('http://localhost:5000/api/configs');
        if (!response.ok) {
            throw new Error('加载配置列表失败');
        }
        const result = await response.json();
        debug('配置列表加载结果', result);
        const data = JSON.parse(result.data);
        
        const tbody = configTable.querySelector('tbody');
        tbody.innerHTML = '';
        
        data.output.forEach(config => {
            const tr = document.createElement('tr');
            tr.innerHTML = `
                <td>${config.file_type}</td>
                <td>${config.kv_fields}</td>
                <td>${config.table_fields}</td>
                <td>
                    <button class="btn btn-danger btn-sm delete-btn" data-type="${config.file_type}">删除</button>
                </td>
            `;
            tbody.appendChild(tr);
        });

        // 绑定删除按钮事件
        document.querySelectorAll('.delete-btn').forEach(btn => {
            btn.addEventListener('click', async () => {
                if (confirm('确定要删除此配置吗？')) {
                    const fileType = btn.dataset.type;
                    debug('删除配置', { fileType });
                    const response = await fetch(`http://localhost:5000/api/configs/${encodeURIComponent(fileType)}`, {
                        method: 'DELETE'
                    });
                    if (!response.ok) {
                        throw new Error('删除配置失败');
                    }
                    await loadConfigs();
                }
            });
        });
    } catch (error) {
        console.error('Error loading configs:', error);
        debug('加载配置列表失败', error);
        alert('加载配置列表失败');
    }
}

// 保存新配置
saveConfigBtn.addEventListener('click', async () => {
    const fileType = document.getElementById('fileTypeInput').value.trim();
    const kvFields = document.getElementById('kvFieldsInput').value.trim();
    const tableFields = document.getElementById('tableFieldsInput').value.trim();

    if (!fileType) {
        alert('文件类型不能为空');
        return;
    }

    try {
        debug('保存新配置', { fileType, kvFields, tableFields });
        const response = await fetch('http://localhost:5000/api/configs', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                file_type: fileType,
                kv_fields: kvFields,
                table_fields: tableFields
            })
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.error || '保存配置失败');
        }

        debug('配置保存成功');
        bootstrap.Modal.getInstance(document.getElementById('configModal')).hide();
        configForm.reset();
        await loadConfigs();
    } catch (error) {
        console.error('Error saving config:', error);
        debug('配置保存失败', error);
        alert(error.message || '保存配置失败');
    }
});

// 检查配置状态
async function checkConfigStatus() {
    try {
        const response = await fetch('/api/config_status');
        const status = await response.json();
        return status;
    } catch (error) {
        console.error('检查配置状态失败:', error);
        return { oss_configured: false, coze_configured: false };
    }
}

// 更新UI状态
function updateUIStatus(status) {
    const configStatusEl = document.getElementById('configStatus');
    if (configStatusEl) {
        configStatusEl.innerHTML = `
            <div class="alert ${status.oss_configured && status.coze_configured ? 'alert-success' : 'alert-warning'}">
                <h5>系统配置状态：</h5>
                <ul class="mb-0">
                    <li>OSS存储配置：${status.oss_configured ? '✅ 已完成' : '❌ 未完成'}</li>
                    <li>Coze API配置：${status.coze_configured ? '✅ 已完成' : '❌ 未完成'}</li>
                </ul>
            </div>
        `;
    }
}

// 加载设置
async function loadSettings() {
    try {
        const response = await fetch('/api/settings');
        const settings = await response.json();
        
        // 填充表单
        document.getElementById('access_key_id').value = settings.ACCESS_KEY_ID || '';
        document.getElementById('access_key_secret').value = settings.ACCESS_KEY_SECRET || '';
        document.getElementById('bucket_name').value = settings.BUCKET_NAME || '';
        document.getElementById('endpoint').value = settings.ENDPOINT || '';
        document.getElementById('region').value = settings.REGION || '';
        document.getElementById('coze_token').value = settings.COZE_TOKEN || '';
        document.getElementById('coze_app_id').value = settings.COZE_APP_ID || '';
        
        // 填充 workflow_ids
        if (settings.WORKFLOW_IDS) {
            document.getElementById('workflow_process_file').value = settings.WORKFLOW_IDS.PROCESS_FILE || '';
            document.getElementById('workflow_show_database').value = settings.WORKFLOW_IDS.SHOW_DATABASE || '';
            document.getElementById('workflow_add_database').value = settings.WORKFLOW_IDS.ADD_DATABASE || '';
            document.getElementById('workflow_delete_database').value = settings.WORKFLOW_IDS.DELETE_DATABASE || '';
        }
    } catch (error) {
        console.error('加载设置失败:', error);
    }
}

// 保存设置
document.getElementById('saveSettingsBtn').addEventListener('click', async () => {
    const settings = {
        ACCESS_KEY_ID: document.getElementById('access_key_id').value,
        ACCESS_KEY_SECRET: document.getElementById('access_key_secret').value,
        BUCKET_NAME: document.getElementById('bucket_name').value,
        ENDPOINT: document.getElementById('endpoint').value,
        REGION: document.getElementById('region').value,
        COZE_TOKEN: document.getElementById('coze_token').value,
        COZE_APP_ID: document.getElementById('coze_app_id').value,
        WORKFLOW_IDS: {
            PROCESS_FILE: document.getElementById('workflow_process_file').value,
            SHOW_DATABASE: document.getElementById('workflow_show_database').value,
            ADD_DATABASE: document.getElementById('workflow_add_database').value,
            DELETE_DATABASE: document.getElementById('workflow_delete_database').value
        }
    };

    try {
        const response = await fetch('/api/settings', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(settings)
        });

        if (response.ok) {
            alert('设置保存成功！');
            const modal = bootstrap.Modal.getInstance(document.getElementById('settingsModal'));
            modal.hide();
            
            // 检查并更新配置状态
            const status = await checkConfigStatus();
            updateUIStatus(status);
            
            // 刷新配置列表
            await loadConfigs();
        } else {
            throw new Error('保存设置失败');
        }
    } catch (error) {
        console.error('保存设置失败:', error);
        alert('保存设置失败，请重试！');
    }
});

// 初始化加载配置列表
document.addEventListener('DOMContentLoaded', async () => {
    debug('页面加载完成，开始初始化');
    loadConfigs();
    loadSettings();
    
    // 初始检查配置状态
    const status = await checkConfigStatus();
    updateUIStatus(status);
});
