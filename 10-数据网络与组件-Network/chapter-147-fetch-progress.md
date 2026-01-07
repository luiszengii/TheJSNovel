《第 147 次记录: 上传进度条的技术之争 —— Fetch 与流式传输的真相》

---

## PR 评审中的分歧

周四上午十点, 你盯着 GitHub 上的 Pull Request, 眉头紧锁。

这是后端开发小王提交的文件上传功能, 代码看起来很简洁——使用了最新的 Fetch API, 支持大文件上传。但问题出现在 PR 下方的评论区, 前端组长老张留下了一条严厉的评论:

> "❌ Fetch API 无法监听上传进度, 这个实现方案不可行。用户上传大文件时看不到进度条, 体验极差。建议改用 XMLHttpRequest。"

小王立刻回复:

> "我查过文档了, Fetch 支持 ReadableStream, 可以监听进度。而且 XMLHttpRequest 是旧 API, 不应该继续使用。"

老张反驳:

> "ReadableStream 只能监听下载进度, 不能监听上传进度。你理解错了。"

小王不服:

> "我测试过了, 可以用 `response.body.getReader()` 读取进度。"

你看着两人的争论, 意识到这不是简单的技术选择问题——这涉及到对 Fetch API 底层机制的理解, 以及上传和下载在 HTTP 协议中的本质区别。

"我们需要实际验证," 你在评论区说, "周四下午 3 点会议室, 我们一起测试两种方案的实际效果。"

---

## 实验对比

周四下午三点, 会议室的投影仪上显示着你准备的测试代码。

"我们先看小王的 Fetch 方案," 你说, 打开第一个测试文件:

```javascript
// 小王的 Fetch 上传方案
async function uploadWithFetch(file) {
    const formData = new FormData();
    formData.append('file', file);

    const response = await fetch('/api/upload', {
        method: 'POST',
        body: formData
    });

    // 尝试监听响应进度 (下载进度)
    const reader = response.body.getReader();
    const contentLength = response.headers.get('Content-Length');
    let receivedLength = 0;

    while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        receivedLength += value.length;
        const percent = (receivedLength / contentLength) * 100;
        console.log(`下载进度: ${percent.toFixed(2)}%`);
    }

    return response.json();
}
```

你选择了一个 50MB 的测试文件, 点击上传按钮。

浏览器的 Network 面板显示上传正在进行, 文件大小逐渐传输, 但控制台却完全没有输出——直到 30 秒后, 文件上传完成, 服务器开始返回响应, 控制台才突然打印:

```
下载进度: 100.00%
```

"看到了吗?" 老张说, "这只是在监听服务器响应的下载进度, 不是文件上传进度。上传的 30 秒里, 用户完全看不到任何进度信息。"

小王不说话了, 盯着屏幕陷入沉思。

"我们再看老张推荐的 XMLHttpRequest 方案," 你切换到第二个测试文件:

```javascript
// 老张的 XMLHttpRequest 上传方案
function uploadWithXHR(file, onProgress) {
    const formData = new FormData();
    formData.append('file', file);

    return new Promise((resolve, reject) => {
        const xhr = new XMLHttpRequest();

        // 监听上传进度
        xhr.upload.onprogress = (e) => {
            if (e.lengthComputable) {
                const percent = (e.loaded / e.total) * 100;
                onProgress(percent, e.loaded, e.total);
            }
        };

        xhr.onload = () => {
            if (xhr.status >= 200 && xhr.status < 300) {
                resolve(JSON.parse(xhr.responseText));
            } else {
                reject(new Error(`Upload failed: ${xhr.status}`));
            }
        };

        xhr.onerror = () => reject(new Error('Network error'));

        xhr.open('POST', '/api/upload');
        xhr.send(formData);
    });
}
```

你再次上传同一个 50MB 文件, 这次控制台立刻开始输出:

```
上传进度: 2.34% (1234567 / 52428800 字节)
上传进度: 5.67% (2971520 / 52428800 字节)
上传进度: 9.12% (4782080 / 52428800 字节)
...
上传进度: 98.45% (51609600 / 52428800 字节)
上传进度: 100.00% (52428800 / 52428800 字节)
```

进度条平滑地从 0% 增长到 100%, 用户可以清晰地看到上传过程。

"确实," 小王承认, "XMLHttpRequest 可以监听上传进度, 但 Fetch 不行。"

---

## 技术真相

会议结束后, 你回到工位, 决定深入研究 Fetch API 的局限性和 XMLHttpRequest 的优势。

你创建了一个对比实验, 理解为什么 Fetch 无法监听上传进度:

```javascript
// Fetch API 的请求和响应流程
async function fetchFlow(file) {
    const formData = new FormData();
    formData.append('file', file);

    // 第 1 阶段: 发送请求 (上传阶段)
    const response = await fetch('/api/upload', {
        method: 'POST',
        body: formData  // ❌ 这个阶段无法监听进度
    });
    // await 会等待整个上传完成, 然后才继续

    // 第 2 阶段: 接收响应 (下载阶段)
    const reader = response.body.getReader();  // ✅ 这个阶段可以监听进度

    while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        // 可以监听下载进度
    }
}
```

"关键在于 `await fetch(...)` 这一行," 你恍然大悟, "这个 Promise 会等待整个请求体上传完成后才 resolve。在上传阶段, 我们无法访问任何进度信息。"

你画了一个流程图:

```
Fetch API 流程:
┌────────────────────────────────────┐
│ fetch() 调用                       │
├────────────────────────────────────┤
│ 上传阶段 (黑盒, 无法监听)          │  ❌ 无法获取进度
│  - 发送请求头                      │
│  - 发送请求体 (FormData)           │
│  - 等待服务器响应                  │
├────────────────────────────────────┤
│ await 完成, 返回 Response 对象     │
├────────────────────────────────────┤
│ 下载阶段 (可监听)                  │  ✅ 可以获取进度
│  - response.body.getReader()       │
│  - 逐块读取响应数据                │
└────────────────────────────────────┘

XMLHttpRequest 流程:
┌────────────────────────────────────┐
│ xhr.send() 调用                    │
├────────────────────────────────────┤
│ 上传阶段 (可监听)                  │  ✅ 可以获取进度
│  - xhr.upload.onprogress           │
│  - 实时获取 loaded/total           │
├────────────────────────────────────┤
│ 下载阶段 (可监听)                  │  ✅ 可以获取进度
│  - xhr.onprogress                  │
│  - 实时获取响应数据                │
└────────────────────────────────────┘
```

你总结了关键区别:

```javascript
// Fetch API: 只能监听下载进度
async function fetchDownloadProgress(url) {
    const response = await fetch(url);  // ❌ 上传阶段 (如果有 body) 无法监听

    const reader = response.body.getReader();
    const contentLength = response.headers.get('Content-Length');
    let receivedLength = 0;

    while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        receivedLength += value.length;
        const percent = (receivedLength / contentLength) * 100;
        console.log(`下载进度: ${percent.toFixed(2)}%`);  // ✅ 下载进度可以监听
    }
}

// XMLHttpRequest: 上传和下载都可以监听
function xhrFullProgress(file, url) {
    const xhr = new XMLHttpRequest();

    // 监听上传进度
    xhr.upload.onprogress = (e) => {
        if (e.lengthComputable) {
            console.log(`上传进度: ${(e.loaded / e.total * 100).toFixed(2)}%`);  // ✅
        }
    };

    // 监听下载进度
    xhr.onprogress = (e) => {
        if (e.lengthComputable) {
            console.log(`下载进度: ${(e.loaded / e.total * 100).toFixed(2)}%`);  // ✅
        }
    };

    xhr.open('POST', url);
    xhr.send(file);
}
```

---

## 性能优化的开始

周五上午九点, 你收到产品经理的消息:

"文件上传功能用户反馈很好, 但有个问题——大文件上传经常失败, 用户抱怨上传了 80% 后突然报错, 然后要重新上传。能不能支持断点续传?"

你意识到这不仅仅是进度显示的问题, 还涉及到大文件上传的可靠性和性能优化。

你开始设计一个完整的上传解决方案:

```javascript
// 完整的上传方案: 进度监听 + 断点续传 + 错误重试
class FileUploader {
    constructor(file, options = {}) {
        this.file = file;
        this.chunkSize = options.chunkSize || 1024 * 1024 * 2;  // 2MB 每块
        this.maxRetries = options.maxRetries || 3;
        this.onProgress = options.onProgress || (() => {});
        this.onComplete = options.onComplete || (() => {});
        this.onError = options.onError || (() => {});

        this.uploadedChunks = new Set();  // 已上传的块
        this.totalChunks = Math.ceil(file.size / this.chunkSize);
    }

    // 分块上传
    async upload() {
        try {
            // 1. 检查是否有未完成的上传
            await this.checkExistingUpload();

            // 2. 分块上传
            for (let i = 0; i < this.totalChunks; i++) {
                if (this.uploadedChunks.has(i)) {
                    continue;  // 跳过已上传的块
                }

                await this.uploadChunk(i);
            }

            // 3. 通知服务器合并文件
            await this.mergeChunks();

            this.onComplete();
        } catch (error) {
            this.onError(error);
        }
    }

    // 检查已上传的块
    async checkExistingUpload() {
        const response = await fetch(`/api/upload/check`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                filename: this.file.name,
                filesize: this.file.size,
                hash: await this.calculateFileHash()
            })
        });

        const data = await response.json();
        this.uploadedChunks = new Set(data.uploadedChunks || []);
    }

    // 上传单个块
    async uploadChunk(chunkIndex, retryCount = 0) {
        const start = chunkIndex * this.chunkSize;
        const end = Math.min(start + this.chunkSize, this.file.size);
        const chunk = this.file.slice(start, end);

        const formData = new FormData();
        formData.append('file', chunk);
        formData.append('filename', this.file.name);
        formData.append('chunkIndex', chunkIndex);
        formData.append('totalChunks', this.totalChunks);
        formData.append('hash', await this.calculateFileHash());

        try {
            await this.uploadChunkWithProgress(formData, chunkIndex);
            this.uploadedChunks.add(chunkIndex);

            // 更新总体进度
            const progress = (this.uploadedChunks.size / this.totalChunks) * 100;
            this.onProgress(progress, this.uploadedChunks.size, this.totalChunks);

        } catch (error) {
            // 错误重试
            if (retryCount < this.maxRetries) {
                console.warn(`块 ${chunkIndex} 上传失败, 重试 ${retryCount + 1}/${this.maxRetries}`);
                await this.delay(1000 * Math.pow(2, retryCount));  // 指数退避
                return this.uploadChunk(chunkIndex, retryCount + 1);
            } else {
                throw new Error(`块 ${chunkIndex} 上传失败, 已达最大重试次数`);
            }
        }
    }

    // 使用 XMLHttpRequest 上传单个块 (监听进度)
    uploadChunkWithProgress(formData, chunkIndex) {
        return new Promise((resolve, reject) => {
            const xhr = new XMLHttpRequest();

            xhr.upload.onprogress = (e) => {
                if (e.lengthComputable) {
                    // 计算当前块的进度
                    const chunkProgress = (e.loaded / e.total) * 100;
                    console.log(`块 ${chunkIndex}: ${chunkProgress.toFixed(2)}%`);
                }
            };

            xhr.onload = () => {
                if (xhr.status >= 200 && xhr.status < 300) {
                    resolve(JSON.parse(xhr.responseText));
                } else {
                    reject(new Error(`HTTP ${xhr.status}`));
                }
            };

            xhr.onerror = () => reject(new Error('Network error'));
            xhr.ontimeout = () => reject(new Error('Timeout'));

            xhr.open('POST', '/api/upload/chunk');
            xhr.timeout = 30000;  // 30 秒超时
            xhr.send(formData);
        });
    }

    // 通知服务器合并文件
    async mergeChunks() {
        const response = await fetch('/api/upload/merge', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                filename: this.file.name,
                totalChunks: this.totalChunks,
                hash: await this.calculateFileHash()
            })
        });

        if (!response.ok) {
            throw new Error('文件合并失败');
        }

        return response.json();
    }

    // 计算文件哈希 (用于断点续传识别)
    async calculateFileHash() {
        // 简化实现: 使用文件名 + 大小 + 修改时间
        return `${this.file.name}-${this.file.size}-${this.file.lastModified}`;
    }

    delay(ms) {
        return new Promise(resolve => setTimeout(resolve, ms));
    }
}
```

---

## 实战验证

周五下午, 你测试了新的上传方案:

```javascript
// 使用示例
const fileInput = document.querySelector('#file');
fileInput.addEventListener('change', (e) => {
    const file = e.target.files[0];

    const uploader = new FileUploader(file, {
        chunkSize: 1024 * 1024 * 2,  // 2MB 每块
        maxRetries: 3,

        onProgress: (percent, uploaded, total) => {
            console.log(`总进度: ${percent.toFixed(2)}% (${uploaded}/${total} 块)`);
            updateProgressBar(percent);
        },

        onComplete: () => {
            console.log('上传完成!');
            showSuccessMessage();
        },

        onError: (error) => {
            console.error('上传失败:', error);
            showErrorMessage(error.message);
        }
    });

    uploader.upload();
});
```

你上传了一个 500MB 的测试文件, 控制台输出:

```
块 0: 100.00%
总进度: 0.40% (1/250 块)
块 1: 100.00%
总进度: 0.80% (2/250 块)
块 2: 100.00%
总进度: 1.20% (3/250 块)
...
块 199: 100.00%
总进度: 80.00% (200/250 块)
```

当进度到达 80% 时, 你故意断开了网络连接, 模拟网络故障。浏览器控制台显示:

```
块 200 上传失败, 重试 1/3
块 200 上传失败, 重试 2/3
块 200 上传失败, 重试 3/3
上传失败: 块 200 上传失败, 已达最大重试次数
```

然后你重新连接网络, 刷新页面, 再次选择同一个文件上传:

```
检查已上传的块...
发现 200 个已上传的块, 从块 200 继续
块 200: 100.00%
总进度: 80.40% (201/250 块)
块 201: 100.00%
总进度: 80.80% (202/250 块)
...
块 249: 100.00%
总进度: 100.00% (250/250 块)
文件合并中...
上传完成!
```

"完美!" 你满意地点头, "断点续传成功了, 从 80% 继续, 而不是从 0% 重新开始。"

---

## 性能对比

你创建了一个性能对比测试, 验证分块上传的优势:

```javascript
// 测试 1: 传统一次性上传 (500MB 文件)
async function traditionalUpload(file) {
    const formData = new FormData();
    formData.append('file', file);

    const startTime = Date.now();

    const xhr = new XMLHttpRequest();

    xhr.upload.onprogress = (e) => {
        if (e.lengthComputable) {
            console.log(`进度: ${(e.loaded / e.total * 100).toFixed(2)}%`);
        }
    };

    xhr.onload = () => {
        const duration = Date.now() - startTime;
        console.log(`传统上传完成, 耗时: ${duration}ms`);
    };

    xhr.open('POST', '/api/upload/traditional');
    xhr.send(formData);
}

// 测试 2: 分块上传 (500MB 文件, 2MB 每块)
async function chunkedUpload(file) {
    const uploader = new FileUploader(file, {
        chunkSize: 1024 * 1024 * 2,

        onComplete: () => {
            console.log('分块上传完成');
        }
    });

    const startTime = Date.now();
    await uploader.upload();
    const duration = Date.now() - startTime;
    console.log(`分块上传完成, 耗时: ${duration}ms`);
}
```

测试结果让你印象深刻:

```
场景 1: 网络稳定
- 传统上传: 62,450ms (62.5 秒)
- 分块上传: 65,230ms (65.2 秒)
差异: +4.4% (分块稍慢, 因为有额外的请求开销)

场景 2: 网络不稳定 (30% 上传时断开 5 秒)
- 传统上传: 从 0% 重新开始, 总耗时 125,800ms (125.8 秒)
- 分块上传: 从 30% 继续, 总耗时 72,340ms (72.3 秒)
差异: -42.5% (分块快得多, 因为支持断点续传)

场景 3: 网络极差 (多次断开)
- 传统上传: 失败, 无法完成
- 分块上传: 成功, 总耗时 156,700ms (156.7 秒)
差异: 传统方案完全失败
```

你总结了分块上传的优势:

```javascript
// 分块上传的核心优势

// 1. 断点续传: 网络中断后可以从中断点继续
// 传统上传: 失败后从 0% 重新开始
// 分块上传: 失败后从最后成功的块继续

// 2. 并发控制: 可以同时上传多个块
class ParallelUploader extends FileUploader {
    async upload() {
        const maxConcurrent = 3;  // 最多 3 个块同时上传

        const chunks = Array.from({ length: this.totalChunks }, (_, i) => i)
            .filter(i => !this.uploadedChunks.has(i));

        // 并发上传
        while (chunks.length > 0) {
            const batch = chunks.splice(0, maxConcurrent);
            await Promise.all(batch.map(i => this.uploadChunk(i)));
        }

        await this.mergeChunks();
    }
}

// 3. 内存优化: 不需要一次性读取整个文件
// 传统上传: FormData 包含整个文件, 内存占用 = 文件大小
// 分块上传: 每次只读取一个块, 内存占用 = 块大小 (如 2MB)

// 4. 进度精确: 块级别的进度反馈
// 传统上传: 只有整体进度
// 分块上传: 每个块的进度 + 整体进度

// 5. 错误隔离: 单个块失败不影响其他块
// 传统上传: 任何错误导致整个上传失败
// 分块上传: 单个块失败可以单独重试
```

---

## 最佳实践方案

你整理了一份完整的上传方案指南:

```javascript
// ✅ 最佳实践 1: 根据场景选择技术
function chooseUploadMethod(file) {
    const fileSize = file.size;

    if (fileSize < 1024 * 1024 * 10) {  // < 10MB
        // 小文件: 使用 XMLHttpRequest 一次性上传
        return uploadWithXHR(file);

    } else if (fileSize < 1024 * 1024 * 100) {  // 10MB - 100MB
        // 中等文件: 分块上传, 串行
        return new FileUploader(file, {
            chunkSize: 1024 * 1024 * 2  // 2MB 每块
        }).upload();

    } else {  // > 100MB
        // 大文件: 分块上传 + 并发
        return new ParallelUploader(file, {
            chunkSize: 1024 * 1024 * 5,  // 5MB 每块
            maxConcurrent: 3  // 最多 3 个块同时上传
        }).upload();
    }
}

// ✅ 最佳实践 2: 完整的错误处理
class RobustUploader extends FileUploader {
    async uploadChunk(chunkIndex, retryCount = 0) {
        try {
            await super.uploadChunk(chunkIndex, retryCount);

        } catch (error) {
            // 分类处理错误
            if (error.message.includes('Network error')) {
                // 网络错误: 等待后重试
                if (retryCount < this.maxRetries) {
                    await this.delay(2000);
                    return this.uploadChunk(chunkIndex, retryCount + 1);
                }
            } else if (error.message.includes('Timeout')) {
                // 超时: 增加超时时间后重试
                if (retryCount < this.maxRetries) {
                    this.timeout = this.timeout * 1.5;  // 增加 50% 超时时间
                    return this.uploadChunk(chunkIndex, retryCount + 1);
                }
            } else if (error.message.includes('HTTP 5')) {
                // 服务器错误: 等待更长时间后重试
                if (retryCount < this.maxRetries) {
                    await this.delay(5000);
                    return this.uploadChunk(chunkIndex, retryCount + 1);
                }
            }

            throw error;
        }
    }
}

// ✅ 最佳实践 3: 优化用户体验
class UXOptimizedUploader extends FileUploader {
    constructor(file, options = {}) {
        super(file, options);

        this.startTime = null;
        this.uploadedBytes = 0;
    }

    async upload() {
        this.startTime = Date.now();

        // 显示预估时间
        setInterval(() => {
            this.updateEstimatedTime();
        }, 1000);

        return super.upload();
    }

    updateEstimatedTime() {
        const elapsedTime = (Date.now() - this.startTime) / 1000;  // 秒
        const uploadSpeed = this.uploadedBytes / elapsedTime;  // 字节/秒

        const remainingBytes = this.file.size - this.uploadedBytes;
        const estimatedSeconds = remainingBytes / uploadSpeed;

        console.log(`预计剩余时间: ${this.formatTime(estimatedSeconds)}`);
        console.log(`上传速度: ${this.formatBytes(uploadSpeed)}/s`);
    }

    formatTime(seconds) {
        const minutes = Math.floor(seconds / 60);
        const secs = Math.floor(seconds % 60);
        return `${minutes}分${secs}秒`;
    }

    formatBytes(bytes) {
        if (bytes < 1024) return `${bytes}B`;
        if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(2)}KB`;
        return `${(bytes / (1024 * 1024)).toFixed(2)}MB`;
    }
}

// ✅ 最佳实践 4: 文件哈希优化
class HashOptimizedUploader extends FileUploader {
    async calculateFileHash() {
        // 大文件: 只计算部分内容的哈希 (首尾 + 采样)
        const chunkSize = 1024 * 1024;  // 1MB
        const chunks = [];

        // 首部 1MB
        chunks.push(this.file.slice(0, chunkSize));

        // 中间采样 (每隔 10MB 采样 1MB)
        const sampleInterval = 1024 * 1024 * 10;
        for (let i = chunkSize; i < this.file.size - chunkSize; i += sampleInterval) {
            chunks.push(this.file.slice(i, i + chunkSize));
        }

        // 尾部 1MB
        chunks.push(this.file.slice(-chunkSize));

        // 计算采样内容的哈希
        const blob = new Blob(chunks);
        const buffer = await blob.arrayBuffer();
        const hashBuffer = await crypto.subtle.digest('SHA-256', buffer);
        const hashArray = Array.from(new Uint8Array(hashBuffer));
        const hashHex = hashArray.map(b => b.toString(16).padStart(2, '0')).join('');

        return hashHex;
    }
}

// ✅ 最佳实践 5: 暂停和恢复上传
class PausableUploader extends FileUploader {
    constructor(file, options = {}) {
        super(file, options);
        this.paused = false;
        this.cancelled = false;
    }

    pause() {
        this.paused = true;
        console.log('上传已暂停');
    }

    resume() {
        this.paused = false;
        console.log('上传已恢复');
    }

    cancel() {
        this.cancelled = true;
        console.log('上传已取消');
    }

    async uploadChunk(chunkIndex, retryCount = 0) {
        // 检查暂停状态
        while (this.paused && !this.cancelled) {
            await this.delay(100);
        }

        // 检查取消状态
        if (this.cancelled) {
            throw new Error('上传已取消');
        }

        return super.uploadChunk(chunkIndex, retryCount);
    }
}
```

---

## 技术总结: Fetch 上传进度的真相

**规则 1: Fetch API 无法监听上传进度**

Fetch API 只能监听响应下载进度, 无法监听请求上传进度。

```javascript
// ❌ 错误理解: 以为 ReadableStream 能监听上传进度
async function wrongUploadProgress(file) {
    const formData = new FormData();
    formData.append('file', file);

    const response = await fetch('/api/upload', {
        method: 'POST',
        body: formData
    });
    // ❌ await 会等待整个上传完成, 无法获取上传进度

    const reader = response.body.getReader();
    // ✅ 这里只能监听下载进度, 不是上传进度

    while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        console.log('下载进度:', value.length);  // ✅ 下载, 不是上传
    }
}

// ✅ 正确: 使用 XMLHttpRequest 监听上传进度
function correctUploadProgress(file) {
    const xhr = new XMLHttpRequest();

    xhr.upload.onprogress = (e) => {
        if (e.lengthComputable) {
            const percent = (e.loaded / e.total) * 100;
            console.log(`上传进度: ${percent.toFixed(2)}%`);  // ✅ 上传进度
        }
    };

    xhr.open('POST', '/api/upload');
    xhr.send(file);
}
```

为什么 Fetch 不支持:
- **设计哲学**: Fetch API 聚焦于简洁的 Promise 接口
- **异步模型**: `await fetch()` 返回的 Promise 代表整个请求完成
- **流式设计**: `response.body` 是响应体的流, 不是请求体
- **历史兼容**: XMLHttpRequest 保留了上传进度监听功能

---

**规则 2: xhr.upload 对象是上传进度的唯一接口**

XMLHttpRequest 提供独立的 `xhr.upload` 对象用于监听上传进度。

```javascript
const xhr = new XMLHttpRequest();

// xhr.upload 对象: 监听上传阶段
xhr.upload.onloadstart = (e) => {
    console.log('上传开始');
};

xhr.upload.onprogress = (e) => {
    if (e.lengthComputable) {
        console.log(`上传中: ${e.loaded} / ${e.total}`);
    }
};

xhr.upload.onload = (e) => {
    console.log('上传完成');
};

xhr.upload.onerror = (e) => {
    console.log('上传失败');
};

xhr.upload.onabort = (e) => {
    console.log('上传中止');
};

xhr.upload.ontimeout = (e) => {
    console.log('上传超时');
};

// xhr 对象本身: 监听下载阶段
xhr.onprogress = (e) => {
    if (e.lengthComputable) {
        console.log(`下载中: ${e.loaded} / ${e.total}`);
    }
};

xhr.onload = () => {
    console.log('下载完成');
};
```

关键区别:
- `xhr.upload.*`: 请求上传阶段的事件
- `xhr.*`: 响应下载阶段的事件
- `e.lengthComputable`: 是否可以计算总长度
- `e.loaded`: 已传输字节数
- `e.total`: 总字节数

---

**规则 3: 分块上传是大文件上传的最佳实践**

对于大文件 (>10MB), 应该使用分块上传策略。

```javascript
// 分块上传的核心流程
class ChunkedUploader {
    constructor(file, chunkSize = 1024 * 1024 * 2) {  // 2MB 默认块大小
        this.file = file;
        this.chunkSize = chunkSize;
        this.totalChunks = Math.ceil(file.size / chunkSize);
    }

    async upload() {
        // 1. 上传每个块
        for (let i = 0; i < this.totalChunks; i++) {
            await this.uploadChunk(i);
        }

        // 2. 通知服务器合并
        await this.mergeChunks();
    }

    async uploadChunk(index) {
        const start = index * this.chunkSize;
        const end = Math.min(start + this.chunkSize, this.file.size);
        const chunk = this.file.slice(start, end);

        const formData = new FormData();
        formData.append('file', chunk);
        formData.append('index', index);
        formData.append('total', this.totalChunks);

        // 使用 XMLHttpRequest 监听单个块的上传进度
        await this.uploadWithXHR(formData);
    }

    uploadWithXHR(formData) {
        return new Promise((resolve, reject) => {
            const xhr = new XMLHttpRequest();

            xhr.upload.onprogress = (e) => {
                if (e.lengthComputable) {
                    const percent = (e.loaded / e.total) * 100;
                    console.log(`块上传进度: ${percent.toFixed(2)}%`);
                }
            };

            xhr.onload = () => {
                if (xhr.status >= 200 && xhr.status < 300) {
                    resolve();
                } else {
                    reject(new Error(`HTTP ${xhr.status}`));
                }
            };

            xhr.onerror = () => reject(new Error('Network error'));

            xhr.open('POST', '/api/upload/chunk');
            xhr.send(formData);
        });
    }

    async mergeChunks() {
        const response = await fetch('/api/upload/merge', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                filename: this.file.name,
                totalChunks: this.totalChunks
            })
        });

        if (!response.ok) {
            throw new Error('合并失败');
        }
    }
}
```

分块上传的优势:
1. **断点续传**: 失败后可以从中断点继续
2. **内存优化**: 不需要一次性加载整个文件
3. **并发上传**: 可以同时上传多个块
4. **错误隔离**: 单个块失败不影响整体
5. **进度精确**: 块级别的进度反馈

---

**规则 4: 断点续传需要文件哈希识别**

断点续传的核心是识别同一个文件的不同上传会话。

```javascript
// 文件哈希计算
class FileHasher {
    static async calculate(file) {
        // 策略 1: 全文件哈希 (适用于小文件)
        if (file.size < 1024 * 1024 * 10) {  // < 10MB
            return await this.fullHash(file);
        }

        // 策略 2: 采样哈希 (适用于大文件)
        return await this.sampledHash(file);
    }

    // 全文件 SHA-256 哈希
    static async fullHash(file) {
        const buffer = await file.arrayBuffer();
        const hashBuffer = await crypto.subtle.digest('SHA-256', buffer);
        return this.bufferToHex(hashBuffer);
    }

    // 采样哈希: 首尾 + 中间采样
    static async sampledHash(file) {
        const chunkSize = 1024 * 1024;  // 1MB
        const chunks = [];

        // 首部 1MB
        chunks.push(file.slice(0, chunkSize));

        // 中间采样 (每隔 10MB 采样 1MB)
        const sampleInterval = 1024 * 1024 * 10;
        for (let i = chunkSize; i < file.size - chunkSize; i += sampleInterval) {
            chunks.push(file.slice(i, i + chunkSize));
        }

        // 尾部 1MB
        chunks.push(file.slice(-chunkSize));

        const blob = new Blob(chunks);
        const buffer = await blob.arrayBuffer();
        const hashBuffer = await crypto.subtle.digest('SHA-256', buffer);
        return this.bufferToHex(hashBuffer);
    }

    static bufferToHex(buffer) {
        const hashArray = Array.from(new Uint8Array(buffer));
        return hashArray.map(b => b.toString(16).padStart(2, '0')).join('');
    }
}

// 断点续传实现
class ResumableUploader extends ChunkedUploader {
    async upload() {
        // 1. 计算文件哈希
        this.fileHash = await FileHasher.calculate(this.file);

        // 2. 查询已上传的块
        const uploadedChunks = await this.checkProgress();

        // 3. 只上传未完成的块
        for (let i = 0; i < this.totalChunks; i++) {
            if (uploadedChunks.includes(i)) {
                console.log(`块 ${i} 已上传, 跳过`);
                continue;
            }

            await this.uploadChunk(i);
        }

        // 4. 合并文件
        await this.mergeChunks();
    }

    async checkProgress() {
        const response = await fetch('/api/upload/check', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                hash: this.fileHash,
                filename: this.file.name,
                filesize: this.file.size
            })
        });

        const data = await response.json();
        return data.uploadedChunks || [];
    }
}
```

哈希策略选择:
- **小文件** (<10MB): 全文件哈希, 准确但慢
- **大文件** (>10MB): 采样哈希, 快但可能冲突
- **极大文件** (>1GB): 首尾 + 稀疏采样, 极快但冲突风险高
- **安全性要求高**: 使用 SHA-256 而非 MD5

---

**规则 5: 错误重试需要指数退避策略**

上传失败后应该使用指数退避算法重试, 避免雪崩效应。

```javascript
class RetryableUploader extends ChunkedUploader {
    constructor(file, options = {}) {
        super(file, options.chunkSize);
        this.maxRetries = options.maxRetries || 3;
        this.baseDelay = options.baseDelay || 1000;  // 基础延迟 1 秒
    }

    async uploadChunk(index, retryCount = 0) {
        try {
            await super.uploadChunk(index);

        } catch (error) {
            if (retryCount >= this.maxRetries) {
                throw new Error(`块 ${index} 上传失败, 已达最大重试次数 ${this.maxRetries}`);
            }

            // 指数退避: 1s, 2s, 4s, 8s, ...
            const delay = this.baseDelay * Math.pow(2, retryCount);

            // 添加随机抖动 (±25%), 避免重试风暴
            const jitter = delay * (0.75 + Math.random() * 0.5);

            console.warn(`块 ${index} 上传失败: ${error.message}`);
            console.warn(`等待 ${jitter.toFixed(0)}ms 后重试 (${retryCount + 1}/${this.maxRetries})`);

            await this.delay(jitter);

            return this.uploadChunk(index, retryCount + 1);
        }
    }

    delay(ms) {
        return new Promise(resolve => setTimeout(resolve, ms));
    }
}
```

指数退避的优势:
- **避免雪崩**: 不会在短时间内发送大量重试请求
- **自适应**: 延迟随重试次数增加而增加
- **随机抖动**: 避免多个客户端同时重试
- **服务器友好**: 给服务器恢复时间

重试策略:
```
重试次数 0: 立即发送
重试次数 1: 延迟 1s + jitter (-250ms ~ +250ms)
重试次数 2: 延迟 2s + jitter (-500ms ~ +500ms)
重试次数 3: 延迟 4s + jitter (-1s ~ +1s)
重试次数 4: 延迟 8s + jitter (-2s ~ +2s)
...
```

---

**规则 6: 并发上传需要限制并发数**

并发上传多个块时, 必须限制并发数, 避免浏览器连接限制。

```javascript
class ParallelUploader extends ChunkedUploader {
    constructor(file, options = {}) {
        super(file, options.chunkSize);
        this.maxConcurrent = options.maxConcurrent || 3;  // 最多 3 个块同时上传
    }

    async upload() {
        const chunks = Array.from({ length: this.totalChunks }, (_, i) => i);

        // 并发控制: 每次最多上传 maxConcurrent 个块
        while (chunks.length > 0) {
            const batch = chunks.splice(0, this.maxConcurrent);

            await Promise.all(batch.map(index => this.uploadChunk(index)));
        }

        await this.mergeChunks();
    }
}

// 更高级的并发控制: 使用任务队列
class QueuedUploader extends ChunkedUploader {
    constructor(file, options = {}) {
        super(file, options.chunkSize);
        this.maxConcurrent = options.maxConcurrent || 3;
        this.queue = [];
        this.running = 0;
    }

    async upload() {
        // 将所有块加入队列
        for (let i = 0; i < this.totalChunks; i++) {
            this.queue.push(i);
        }

        // 启动并发上传
        const workers = Array.from({ length: this.maxConcurrent }, () => this.worker());

        await Promise.all(workers);
        await this.mergeChunks();
    }

    async worker() {
        while (this.queue.length > 0) {
            const index = this.queue.shift();
            if (index === undefined) break;

            this.running++;
            try {
                await this.uploadChunk(index);
            } finally {
                this.running--;
            }
        }
    }
}
```

并发限制的原因:
- **浏览器限制**: HTTP/1.1 每个域名最多 6 个并发连接
- **服务器压力**: 过多并发请求可能导致服务器过载
- **内存占用**: 每个并发请求占用内存
- **网络带宽**: 过多并发可能导致带宽竞争

推荐并发数:
- **小文件** (<10MB): 1-2 个并发
- **中等文件** (10MB-100MB): 2-3 个并发
- **大文件** (>100MB): 3-5 个并发
- **极大文件** (>1GB): 5-8 个并发 (HTTP/2 环境)

---

**规则 7: 上传状态需要持久化存储**

断点续传需要将上传状态保存到 localStorage 或 IndexedDB。

```javascript
class PersistentUploader extends ChunkedUploader {
    constructor(file, options = {}) {
        super(file, options.chunkSize);
        this.storageKey = `upload_${this.fileHash}`;
    }

    async upload() {
        // 1. 加载已保存的状态
        const savedState = this.loadState();

        // 2. 上传未完成的块
        for (let i = 0; i < this.totalChunks; i++) {
            if (savedState.uploadedChunks.includes(i)) {
                continue;
            }

            await this.uploadChunk(i);

            // 3. 保存状态
            savedState.uploadedChunks.push(i);
            this.saveState(savedState);
        }

        // 4. 合并完成后清除状态
        await this.mergeChunks();
        this.clearState();
    }

    loadState() {
        const saved = localStorage.getItem(this.storageKey);
        if (saved) {
            return JSON.parse(saved);
        }

        return {
            filename: this.file.name,
            filesize: this.file.size,
            fileHash: this.fileHash,
            totalChunks: this.totalChunks,
            uploadedChunks: [],
            startTime: Date.now()
        };
    }

    saveState(state) {
        localStorage.setItem(this.storageKey, JSON.stringify(state));
    }

    clearState() {
        localStorage.removeItem(this.storageKey);
    }
}
```

持久化策略:
- **localStorage**: 简单快速, 但有 5-10MB 限制
- **IndexedDB**: 容量大, 但 API 复杂
- **SessionStorage**: 关闭标签页后清除
- **服务器端**: 最可靠, 但需要额外请求

---

**规则 8: 用户体验优化是上传功能的关键**

完整的上传功能必须考虑用户体验。

```javascript
class UXOptimizedUploader extends ChunkedUploader {
    constructor(file, options = {}) {
        super(file, options.chunkSize);
        this.onProgress = options.onProgress || (() => {});
        this.startTime = null;
        this.uploadedBytes = 0;
    }

    async upload() {
        this.startTime = Date.now();

        // 定期更新预估时间
        const timer = setInterval(() => {
            this.updateEstimate();
        }, 1000);

        try {
            await super.upload();
        } finally {
            clearInterval(timer);
        }
    }

    async uploadChunk(index) {
        const start = index * this.chunkSize;
        const end = Math.min(start + this.chunkSize, this.file.size);
        const chunkSize = end - start;

        await super.uploadChunk(index);

        this.uploadedBytes += chunkSize;

        // 更新进度
        const percent = (this.uploadedBytes / this.file.size) * 100;
        this.onProgress({
            percent: percent,
            uploaded: this.uploadedBytes,
            total: this.file.size,
            chunkIndex: index,
            totalChunks: this.totalChunks
        });
    }

    updateEstimate() {
        const elapsedMs = Date.now() - this.startTime;
        const elapsedSec = elapsedMs / 1000;

        // 上传速度 (字节/秒)
        const speed = this.uploadedBytes / elapsedSec;

        // 剩余字节
        const remainingBytes = this.file.size - this.uploadedBytes;

        // 预估剩余时间 (秒)
        const estimatedSec = remainingBytes / speed;

        console.log(`上传速度: ${this.formatBytes(speed)}/s`);
        console.log(`预计剩余: ${this.formatTime(estimatedSec)}`);
    }

    formatBytes(bytes) {
        if (bytes < 1024) return `${bytes}B`;
        if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(2)}KB`;
        if (bytes < 1024 * 1024 * 1024) return `${(bytes / (1024 * 1024)).toFixed(2)}MB`;
        return `${(bytes / (1024 * 1024 * 1024)).toFixed(2)}GB`;
    }

    formatTime(seconds) {
        if (seconds < 60) return `${Math.floor(seconds)}秒`;
        if (seconds < 3600) {
            const min = Math.floor(seconds / 60);
            const sec = Math.floor(seconds % 60);
            return `${min}分${sec}秒`;
        }
        const hour = Math.floor(seconds / 3600);
        const min = Math.floor((seconds % 3600) / 60);
        return `${hour}小时${min}分`;
    }
}
```

用户体验要素:
1. **实时进度**: 显示当前上传百分比
2. **速度显示**: 显示当前上传速度
3. **预估时间**: 显示预计剩余时间
4. **暂停/恢复**: 允许用户控制上传
5. **错误提示**: 清晰的错误信息和重试选项
6. **成功反馈**: 上传完成后的明确提示

---

**事故档案编号**: NETWORK-2024-1947
**影响范围**: Fetch API, XMLHttpRequest, 文件上传进度, 分块上传, 断点续传
**根本原因**: Fetch API 设计上无法监听上传进度, 大文件上传缺乏可靠性保障
**学习成本**: 高 (需理解 HTTP 上传下载机制、并发控制、错误重试策略)

这是 JavaScript 世界第 147 次被记录的网络与数据事故。Fetch API 无法监听上传进度, 只能监听下载进度。XMLHttpRequest 的 `xhr.upload` 对象是监听上传进度的唯一标准接口。对于大文件上传, 分块上传是最佳实践, 支持断点续传、并发控制和错误隔离。断点续传需要文件哈希识别同一文件的不同上传会话。错误重试应使用指数退避策略避免雪崩效应。并发上传需要限制并发数, 避免浏览器连接限制和服务器压力。上传状态需要持久化存储以支持跨会话恢复。完整的上传功能必须优化用户体验, 包括实时进度、速度显示、预估时间和错误处理。理解上传和下载在 HTTP 协议中的本质区别, 选择合适的 API 和策略是构建可靠文件上传功能的基础。

---
