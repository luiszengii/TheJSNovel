《第 152 次记录: 文件上传的续命之术 —— 断点续传的三种实现》

---

## 架构会议的分歧

周二下午三点, 会议室的白板上写着 "大文件上传优化方案"。

你坐在会议桌前, 看着产品经理小王展示的用户反馈: "上传 500MB 视频到 80% 时网络断了, 用户不得不从 0% 重新开始。这个问题每天有 50+ 投诉。"

技术总监老李敲了敲桌子: "我们需要断点续传功能, 这是刚需。各位有什么方案?"

前端小陈第一个发言: "我调研过了, 有三种主流方案。" 他在白板上写下:

```
方案 1: 基于 Range 请求头 (单文件分段上传)
方案 2: 分块上传 + 服务端合并 (多请求)
方案 3: WebRTC Data Channel (点对点)
```

后端老张立刻反对: "方案 1 不行, Range 请求头是为下载设计的, 上传场景不适用。方案 3 太复杂, 我们没有 WebRTC 基础设施。"

"那只能用方案 2 了?" 小陈问。

"但方案 2 有个问题, " 你插话, "如何识别同一个文件的不同上传会话? 用户可能今天上传到 50%, 明天换了个浏览器继续上传, 服务器怎么知道这是同一个文件?"

会议室陷入沉默。

老李看向你: "你有想法?"

你走到白板前, 画了一个流程图: "关键是文件哈希。我们计算文件的 SHA-256 哈希值作为唯一标识, 服务器根据哈希值判断是否是同一个文件。"

"但是, " 小陈质疑, "计算 500MB 文件的哈希值不会很慢吗? 用户等不了。"

"所以要用采样哈希, " 你解释, "不计算整个文件, 只计算首部、尾部和中间采样点。这样既快速, 又能保证唯一性。"

老张点头: "听起来可行。但还有个问题: 如果用户上传到 80%, 然后关闭浏览器, 再打开时如何恢复进度? 浏览器刷新后内存里的数据都没了。"

"持久化, " 你说, "用 localStorage 保存上传状态。每上传完一个块, 就更新 localStorage。下次打开页面时, 先查询 localStorage 和服务器, 看哪些块已经上传成功, 只上传剩余的块。"

老李思考了一会儿: "方案可行。但我们需要看到代码实现, 不能只停留在理论层面。你能在这周五之前做一个 Demo 吗?"

"可以, " 你说, "我今天就开始写。"

---

## 三种方案的技术验证

周三上午, 你在自己的机器上搭建了测试环境。

首先你实现了方案 1 (Range 请求), 想验证老张说的 "不适用" 是否正确:

```javascript
// 方案 1: 尝试用 Range 请求头上传 (失败案例)
async function uploadWithRange(file) {
    const chunkSize = 1024 * 1024 * 2;  // 2MB

    for (let start = 0; start < file.size; start += chunkSize) {
        const end = Math.min(start + chunkSize, file.size);
        const chunk = file.slice(start, end);

        try {
            const response = await fetch('/upload', {
                method: 'POST',
                headers: {
                    'Content-Range': `bytes ${start}-${end - 1}/${file.size}`,
                    'Content-Type': 'application/octet-stream'
                },
                body: chunk
            });

            if (!response.ok) {
                console.error('上传失败:', response.status);
                break;
            }

        } catch (error) {
            console.error('网络错误:', error);
            break;
        }
    }
}
```

你测试了这个方案, 发现两个致命问题:

```
问题 1: Content-Range 请求头在 POST 请求中不被标准支持
- 浏览器发送了请求, 但服务器不知道如何处理
- Nginx 默认配置会拒绝带 Content-Range 的 POST 请求

问题 2: 无法判断文件身份
- 服务器收到多个块, 但不知道它们属于哪个文件
- 无法实现断点续传, 因为没有唯一标识
```

"老张说得对, " 你在笔记本上记下, "Range 请求头确实不适合上传场景。"

然后你实现了方案 2 (分块上传):

```javascript
// 方案 2: 分块上传 + 文件哈希识别 (可行方案)
class ResumableUploader {
    constructor(file, options = {}) {
        this.file = file;
        this.chunkSize = options.chunkSize || 1024 * 1024 * 2;  // 2MB
        this.totalChunks = Math.ceil(file.size / this.chunkSize);
        this.uploadedChunks = new Set();
        this.fileHash = null;
    }

    // 计算文件哈希 (采样策略)
    async calculateHash() {
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
        if (this.file.size > chunkSize) {
            chunks.push(this.file.slice(-chunkSize));
        }

        // 计算 SHA-256
        const blob = new Blob(chunks);
        const buffer = await blob.arrayBuffer();
        const hashBuffer = await crypto.subtle.digest('SHA-256', buffer);
        const hashArray = Array.from(new Uint8Array(hashBuffer));
        this.fileHash = hashArray.map(b => b.toString(16).padStart(2, '0')).join('');

        return this.fileHash;
    }

    // 查询服务器已上传的块
    async checkProgress() {
        const response = await fetch('/upload/check', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                fileHash: this.fileHash,
                fileName: this.file.name,
                fileSize: this.file.size,
                totalChunks: this.totalChunks
            })
        });

        const data = await response.json();
        this.uploadedChunks = new Set(data.uploadedChunks || []);

        console.log(`服务器已有 ${this.uploadedChunks.size} 个块`);
        return this.uploadedChunks;
    }

    // 上传单个块
    async uploadChunk(index) {
        const start = index * this.chunkSize;
        const end = Math.min(start + this.chunkSize, this.file.size);
        const chunk = this.file.slice(start, end);

        const formData = new FormData();
        formData.append('file', chunk);
        formData.append('fileHash', this.fileHash);
        formData.append('fileName', this.file.name);
        formData.append('chunkIndex', index);
        formData.append('totalChunks', this.totalChunks);

        const response = await fetch('/upload/chunk', {
            method: 'POST',
            body: formData
        });

        if (!response.ok) {
            throw new Error(`块 ${index} 上传失败: HTTP ${response.status}`);
        }

        return await response.json();
    }

    // 执行上传
    async upload() {
        // 1. 计算文件哈希
        console.log('计算文件哈希...');
        const hashStart = Date.now();
        await this.calculateHash();
        console.log(`哈希计算完成 (${Date.now() - hashStart}ms): ${this.fileHash}`);

        // 2. 查询服务器进度
        await this.checkProgress();

        // 3. 上传未完成的块
        for (let i = 0; i < this.totalChunks; i++) {
            if (this.uploadedChunks.has(i)) {
                console.log(`块 ${i} 已上传, 跳过`);
                continue;
            }

            try {
                await this.uploadChunk(i);
                this.uploadedChunks.add(i);
                console.log(`块 ${i} 上传成功 (${this.uploadedChunks.size}/${this.totalChunks})`);

                // 保存进度到 localStorage
                this.saveProgress();

            } catch (error) {
                console.error(`块 ${i} 上传失败:`, error);
                throw error;
            }
        }

        // 4. 通知服务器合并文件
        await this.mergeChunks();

        // 5. 清理进度记录
        this.clearProgress();

        console.log('文件上传完成!');
    }

    // 保存进度到 localStorage
    saveProgress() {
        const progress = {
            fileHash: this.fileHash,
            fileName: this.file.name,
            fileSize: this.file.size,
            totalChunks: this.totalChunks,
            uploadedChunks: Array.from(this.uploadedChunks),
            lastUpdate: Date.now()
        };

        localStorage.setItem(`upload_${this.fileHash}`, JSON.stringify(progress));
    }

    // 加载进度从 localStorage
    static loadProgress(fileHash) {
        const saved = localStorage.getItem(`upload_${fileHash}`);
        return saved ? JSON.parse(saved) : null;
    }

    // 清理进度记录
    clearProgress() {
        localStorage.removeItem(`upload_${this.fileHash}`);
    }

    // 通知服务器合并文件
    async mergeChunks() {
        const response = await fetch('/upload/merge', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                fileHash: this.fileHash,
                fileName: this.file.name,
                totalChunks: this.totalChunks
            })
        });

        if (!response.ok) {
            throw new Error('文件合并失败');
        }

        return await response.json();
    }
}
```

你用一个 200MB 的测试文件验证了这个实现:

```javascript
// 测试: 断点续传
const fileInput = document.querySelector('#file');
fileInput.addEventListener('change', async (e) => {
    const file = e.target.files[0];

    const uploader = new ResumableUploader(file, {
        chunkSize: 1024 * 1024 * 2  // 2MB
    });

    try {
        await uploader.upload();
        console.log('上传成功!');
    } catch (error) {
        console.error('上传失败:', error);
    }
});
```

测试结果:

```
第 1 次上传 (完整流程):
- 哈希计算: 245ms
- 上传块 0-49 (50 个块, 每块 2MB)
- 总耗时: 28.3 秒

第 2 次上传 (模拟断网后恢复):
- 手动中断网络 (上传到块 30)
- 刷新页面, 重新选择文件
- 哈希计算: 242ms (几乎相同)
- 查询服务器: 已上传 30 个块
- 只上传块 30-49 (20 个块)
- 总耗时: 11.7 秒 (节省了 58.7% 时间)
```

"完美, " 你满意地点头, "断点续传成功了。"

---

## 错误重试与并发优化

周四上午, 你在测试中发现了新问题。

当你故意模拟不稳定网络 (随机丢包 30%) 时, 上传过程经常卡死——某个块上传失败后, 整个流程就停止了。

"需要错误重试机制, " 你在代码中添加了重试逻辑:

```javascript
// 增强版: 支持错误重试
class RobustUploader extends ResumableUploader {
    constructor(file, options = {}) {
        super(file, options);
        this.maxRetries = options.maxRetries || 3;
        this.retryDelay = options.retryDelay || 1000;  // 基础延迟 1 秒
    }

    // 上传单个块 (带重试)
    async uploadChunk(index, retryCount = 0) {
        try {
            return await super.uploadChunk(index);

        } catch (error) {
            if (retryCount >= this.maxRetries) {
                throw new Error(`块 ${index} 上传失败 (已重试 ${this.maxRetries} 次): ${error.message}`);
            }

            // 指数退避 + 随机抖动
            const delay = this.retryDelay * Math.pow(2, retryCount);
            const jitter = delay * (0.5 + Math.random() * 0.5);

            console.warn(`块 ${index} 上传失败, ${jitter.toFixed(0)}ms 后重试 (${retryCount + 1}/${this.maxRetries})`);

            await this.delay(jitter);

            return this.uploadChunk(index, retryCount + 1);
        }
    }

    delay(ms) {
        return new Promise(resolve => setTimeout(resolve, ms));
    }
}
```

测试结果 (30% 丢包环境):

```
使用 ResumableUploader (无重试):
- 50 个块中 18 个失败
- 上传中断

使用 RobustUploader (3 次重试):
- 50 个块全部成功
- 重试次数: 块 7 (1次), 块 12 (2次), 块 23 (1次), ...
- 总耗时: 42.5 秒 (比正常慢 50%, 但成功率 100%)
```

然后你想到另一个优化: 并发上传多个块。

"现在是串行上传, 一个块一个块来, 效率太低了。如果并发上传 3 个块, 应该能快不少。" 你实现了并发控制:

```javascript
// 并发上传版本
class ConcurrentUploader extends RobustUploader {
    constructor(file, options = {}) {
        super(file, options);
        this.maxConcurrent = options.maxConcurrent || 3;
    }

    async upload() {
        // 1. 计算哈希并查询进度
        await this.calculateHash();
        await this.checkProgress();

        // 2. 构建待上传块列表
        const pendingChunks = [];
        for (let i = 0; i < this.totalChunks; i++) {
            if (!this.uploadedChunks.has(i)) {
                pendingChunks.push(i);
            }
        }

        console.log(`待上传 ${pendingChunks.length} 个块`);

        // 3. 并发上传
        while (pendingChunks.length > 0) {
            // 取出最多 maxConcurrent 个块
            const batch = pendingChunks.splice(0, this.maxConcurrent);

            // 并发上传这一批
            await Promise.all(batch.map(async (index) => {
                try {
                    await this.uploadChunk(index);
                    this.uploadedChunks.add(index);
                    this.saveProgress();
                    console.log(`块 ${index} 上传成功`);
                } catch (error) {
                    console.error(`块 ${index} 最终失败:`, error);
                    throw error;
                }
            }));
        }

        // 4. 合并文件
        await this.mergeChunks();
        this.clearProgress();

        console.log('上传完成!');
    }
}
```

性能对比测试 (200MB 文件, 稳定网络):

```
串行上传 (ResumableUploader):
- 50 个块依次上传
- 总耗时: 28.3 秒

并发上传 (ConcurrentUploader, 并发数 3):
- 每批 3 个块同时上传
- 总耗时: 12.8 秒 (快了 54.8%)

并发上传 (并发数 5):
- 每批 5 个块同时上传
- 总耗时: 9.2 秒 (快了 67.5%)
- ⚠️ 但浏览器连接数限制可能导致其他请求阻塞
```

"并发数 3 是个平衡点, " 你在笔记中记录, "既能提升速度, 又不会占用太多浏览器连接。"

---

## 周五下午的 Demo 演示

周五下午两点, 你在会议室演示了完整的实现。

"我准备了三个测试场景, " 你说着, 打开演示页面。

**场景 1: 正常上传**

你选择了一个 300MB 的视频文件, 点击上传按钮。控制台输出:

```
计算文件哈希...
哈希计算完成 (287ms): a3f5b8c2d9e1f4a7b6c3d8e2f5a9b7c4d3e8f1a6b9c5d2e7f4a8b3c6d9e5f2a
服务器已有 0 个块
块 0 上传成功 (1/150)
块 1 上传成功 (2/150)
块 2 上传成功 (3/150)
...
块 149 上传成功 (150/150)
文件合并中...
上传完成!
总耗时: 38.2 秒
```

**场景 2: 断点续传**

你在上传到 40% 时, 手动关闭了网络连接。页面显示错误。

然后你刷新页面, 重新打开网络, 再次选择同一个文件上传:

```
计算文件哈希...
哈希计算完成 (284ms): a3f5b8c2d9e1f4a7b6c3d8e2f5a9b7c4d3e8f1a6b9c5d2e7f4a8b3c6d9e5f2a
服务器已有 60 个块
块 0-59 已上传, 跳过
块 60 上传成功 (61/150)
块 61 上传成功 (62/150)
...
块 149 上传成功 (150/150)
文件合并中...
上传完成!
总耗时: 23.1 秒 (节省了 39.5%)
```

小王 (产品经理) 眼睛亮了: "太好了! 用户不用重新上传了。"

**场景 3: 错误重试**

你模拟了不稳定网络环境 (30% 丢包):

```
块 0 上传成功 (1/150)
块 1 上传失败, 1024ms 后重试 (1/3)
块 1 上传成功 (2/150)
块 2 上传成功 (3/150)
...
块 37 上传失败, 1087ms 后重试 (1/3)
块 37 上传失败, 2134ms 后重试 (2/3)
块 37 上传成功 (38/150)
...
块 149 上传成功 (150/150)
上传完成!
总耗时: 52.7 秒 (正常网络: 38.2 秒)
```

老李点头: "重试机制很必要。但我注意到你用的是指数退避, 为什么?"

"避免重试风暴, " 你解释, "如果服务器暂时过载, 所有客户端同时重试会导致雪崩效应。指数退避 + 随机抖动可以分散重试时间。"

老张问: "那服务器端怎么处理这些块? 需要什么样的 API?"

你切换到服务器端代码 (Node.js 示例):

```javascript
// 服务器端实现 (Node.js + Express)
const express = require('express');
const multer = require('multer');
const fs = require('fs').promises;
const path = require('path');

const app = express();
const upload = multer({ dest: 'uploads/chunks/' });

// 临时存储目录
const TEMP_DIR = 'uploads/chunks/';
const MERGED_DIR = 'uploads/merged/';

// API 1: 查询上传进度
app.post('/upload/check', express.json(), async (req, res) => {
    const { fileHash } = req.body;

    // 查询该文件已上传的块
    const chunkDir = path.join(TEMP_DIR, fileHash);

    try {
        const files = await fs.readdir(chunkDir);
        const uploadedChunks = files
            .filter(f => f.startsWith('chunk-'))
            .map(f => parseInt(f.replace('chunk-', '')));

        res.json({
            success: true,
            uploadedChunks: uploadedChunks
        });
    } catch (error) {
        // 目录不存在说明还没上传过
        res.json({
            success: true,
            uploadedChunks: []
        });
    }
});

// API 2: 上传单个块
app.post('/upload/chunk', upload.single('file'), async (req, res) => {
    const { fileHash, chunkIndex, totalChunks } = req.body;
    const chunk = req.file;

    // 创建文件专属目录
    const chunkDir = path.join(TEMP_DIR, fileHash);
    await fs.mkdir(chunkDir, { recursive: true });

    // 保存块文件
    const chunkPath = path.join(chunkDir, `chunk-${chunkIndex}`);
    await fs.rename(chunk.path, chunkPath);

    res.json({
        success: true,
        chunkIndex: parseInt(chunkIndex)
    });
});

// API 3: 合并文件
app.post('/upload/merge', express.json(), async (req, res) => {
    const { fileHash, fileName, totalChunks } = req.body;

    const chunkDir = path.join(TEMP_DIR, fileHash);
    const mergedPath = path.join(MERGED_DIR, fileName);

    try {
        // 创建输出目录
        await fs.mkdir(MERGED_DIR, { recursive: true });

        // 创建写入流
        const writeStream = require('fs').createWriteStream(mergedPath);

        // 依次读取并写入每个块
        for (let i = 0; i < totalChunks; i++) {
            const chunkPath = path.join(chunkDir, `chunk-${i}`);
            const chunkData = await fs.readFile(chunkPath);
            writeStream.write(chunkData);
        }

        writeStream.end();

        // 等待写入完成
        await new Promise((resolve, reject) => {
            writeStream.on('finish', resolve);
            writeStream.on('error', reject);
        });

        // 删除临时块文件
        await fs.rm(chunkDir, { recursive: true });

        res.json({
            success: true,
            filePath: mergedPath
        });

    } catch (error) {
        res.status(500).json({
            success: false,
            error: error.message
        });
    }
});

app.listen(3000, () => {
    console.log('服务器运行在 http://localhost:3000');
});
```

老张仔细看了代码: "块的顺序怎么保证? 如果块 5 比块 4 先上传完成, 服务器会等待吗?"

"会等待, " 你指着合并代码, "合并时是按照 `chunk-0`, `chunk-1`, `chunk-2` 的顺序依次读取, 所以最终文件一定是正确的。客户端可以乱序上传, 但服务器合并时会按序拼接。"

老李最后问: "如果用户上传了一半, 然后再也不继续了怎么办? 服务器上的临时块会一直占用空间吗?"

"需要定期清理, " 你说, "可以设置一个定时任务, 删除超过 7 天未完成的块文件。或者在 `/upload/check` API 中返回块的上传时间, 客户端决定是否重新上传。"

会议结束时, 老李拍了拍你的肩膀: "方案通过。下周开始接入生产环境。"

---

## 知识档案: 可恢复文件上传的八个核心机制

**规则 1: 文件哈希是断点续传的唯一标识**

你终于理解了断点续传的核心: 必须有一个稳定的、跨会话的文件标识符。文件名不可靠 (用户可能重命名), 文件大小不唯一 (可能有同样大小的文件), 只有内容哈希才能准确识别同一个文件。

```javascript
// 文件哈希计算
async function calculateFileHash(file) {
    // 对于小文件 (<10MB), 计算全文件哈希
    if (file.size < 1024 * 1024 * 10) {
        const buffer = await file.arrayBuffer();
        const hashBuffer = await crypto.subtle.digest('SHA-256', buffer);
        return bufferToHex(hashBuffer);
    }

    // 对于大文件, 使用采样哈希
    const chunks = [
        file.slice(0, 1024 * 1024),  // 首部 1MB
        file.slice(-1024 * 1024)      // 尾部 1MB
    ];

    // 中间采样 (每隔 10MB 采样 1MB)
    for (let i = 1024 * 1024; i < file.size - 1024 * 1024; i += 1024 * 1024 * 10) {
        chunks.push(file.slice(i, i + 1024 * 1024));
    }

    const blob = new Blob(chunks);
    const buffer = await blob.arrayBuffer();
    const hashBuffer = await crypto.subtle.digest('SHA-256', buffer);
    return bufferToHex(hashBuffer);
}

function bufferToHex(buffer) {
    return Array.from(new Uint8Array(buffer))
        .map(b => b.toString(16).padStart(2, '0'))
        .join('');
}
```

为什么采样哈希足够:
- **速度**: 只计算 3-5MB 数据而非整个 500MB 文件
- **唯一性**: 首部 + 尾部 + 中间采样点, 碰撞概率极低
- **一致性**: 同一文件在不同设备上计算的哈希相同

---

**规则 2: 分块大小影响上传效率和恢复粒度**

块太大: 单个块失败重传代价高, 断点续传优势不明显。
块太小: 请求数量多, HTTP 开销大, 服务器压力大。

```javascript
// 块大小选择策略
function chooseChunkSize(fileSize) {
    if (fileSize < 1024 * 1024 * 10) {  // <10MB
        return 1024 * 1024 * 1;  // 1MB
    } else if (fileSize < 1024 * 1024 * 100) {  // 10MB-100MB
        return 1024 * 1024 * 2;  // 2MB
    } else if (fileSize < 1024 * 1024 * 1000) {  // 100MB-1GB
        return 1024 * 1024 * 5;  // 5MB
    } else {  // >1GB
        return 1024 * 1024 * 10;  // 10MB
    }
}

// 示例
const file = { size: 500 * 1024 * 1024 };  // 500MB
const chunkSize = chooseChunkSize(file.size);
console.log(chunkSize);  // 5MB
console.log(Math.ceil(file.size / chunkSize));  // 100 个块
```

块大小对比:

| 文件大小 | 块大小 | 块数量 | 总请求数 | 单块失败代价 |
|---------|--------|--------|---------|------------|
| 100MB | 1MB | 100 | 102 (check + 100 + merge) | 低 (1MB 重传) |
| 100MB | 10MB | 10 | 12 | 高 (10MB 重传) |
| 500MB | 5MB | 100 | 102 | 适中 |

---

**规则 3: 并发上传需要限制并发数以避免资源竞争**

浏览器对同一域名有并发连接限制 (HTTP/1.1 通常是 6 个), 过多并发会导致:
- 阻塞其他正常请求 (如 API 调用、静态资源加载)
- 服务器压力增大
- 内存占用增加 (每个并发块占用内存)

```javascript
class ConcurrentUploader {
    constructor(file, options = {}) {
        this.file = file;
        this.maxConcurrent = options.maxConcurrent || 3;  // 默认 3 个并发
    }

    async uploadWithConcurrency(chunks) {
        const queue = [...chunks];
        const results = [];

        // 创建 worker 函数
        const worker = async () => {
            while (queue.length > 0) {
                const index = queue.shift();
                if (index === undefined) break;

                try {
                    const result = await this.uploadChunk(index);
                    results.push({ index, success: true, result });
                } catch (error) {
                    results.push({ index, success: false, error });
                    throw error;
                }
            }
        };

        // 启动多个 worker
        const workers = Array.from(
            { length: this.maxConcurrent },
            () => worker()
        );

        await Promise.all(workers);
        return results;
    }
}
```

并发数选择:
- **小文件** (< 10MB): 1-2 并发 (总时间短, 不需要高并发)
- **中等文件** (10MB-100MB): 2-3 并发 (平衡速度和资源)
- **大文件** (> 100MB): 3-5 并发 (长时间上传, 提升效率)
- **极大文件** (> 1GB): 5-8 并发 (仅限 HTTP/2 环境)

---

**规则 4: 错误重试必须使用指数退避避免雪崩**

所有客户端同时重试会导致服务器雪崩。指数退避 + 随机抖动可以分散重试时间。

```javascript
class RetryableUploader {
    constructor(file, options = {}) {
        this.file = file;
        this.maxRetries = options.maxRetries || 3;
        this.baseDelay = options.baseDelay || 1000;  // 基础延迟 1 秒
    }

    async uploadChunkWithRetry(index, attempt = 0) {
        try {
            return await this.uploadChunk(index);
        } catch (error) {
            if (attempt >= this.maxRetries) {
                throw new Error(`块 ${index} 上传失败 (已重试 ${this.maxRetries} 次)`);
            }

            // 指数退避: 1s → 2s → 4s → 8s
            const delay = this.baseDelay * Math.pow(2, attempt);

            // 随机抖动: ±50%
            const jitter = delay * (0.5 + Math.random());

            console.warn(`块 ${index} 失败, ${jitter.toFixed(0)}ms 后重试 (${attempt + 1}/${this.maxRetries})`);

            await this.delay(jitter);

            return this.uploadChunkWithRetry(index, attempt + 1);
        }
    }

    delay(ms) {
        return new Promise(resolve => setTimeout(resolve, ms));
    }
}
```

重试策略对比:

| 策略 | 重试间隔 | 优点 | 缺点 |
|------|---------|------|------|
| 固定间隔 | 1s, 1s, 1s | 简单 | 雪崩风险高 |
| 线性退避 | 1s, 2s, 3s | 较温和 | 仍有雪崩风险 |
| 指数退避 | 1s, 2s, 4s | 分散重试 | 后期等待久 |
| 指数退避 + 抖动 | 1s±50%, 2s±50%, 4s±50% | ✅ 最佳方案 | 稍复杂 |

---

**规则 5: localStorage 持久化上传状态支持跨会话恢复**

用户刷新页面或关闭浏览器后, 内存中的上传状态会丢失。localStorage 可以保存状态, 实现跨会话恢复。

```javascript
class PersistentUploader {
    saveProgress() {
        const progress = {
            fileHash: this.fileHash,
            fileName: this.file.name,
            fileSize: this.file.size,
            chunkSize: this.chunkSize,
            totalChunks: this.totalChunks,
            uploadedChunks: Array.from(this.uploadedChunks),
            lastUpdate: Date.now()
        };

        localStorage.setItem(`upload_${this.fileHash}`, JSON.stringify(progress));
    }

    static loadProgress(fileHash) {
        const saved = localStorage.getItem(`upload_${fileHash}`);
        if (!saved) return null;

        const progress = JSON.parse(saved);

        // 检查是否过期 (7 天)
        const age = Date.now() - progress.lastUpdate;
        if (age > 7 * 24 * 60 * 60 * 1000) {
            localStorage.removeItem(`upload_${fileHash}`);
            return null;
        }

        return progress;
    }

    clearProgress() {
        localStorage.removeItem(`upload_${this.fileHash}`);
    }

    async upload() {
        await this.calculateHash();

        // 尝试从 localStorage 恢复进度
        const savedProgress = PersistentUploader.loadProgress(this.fileHash);
        if (savedProgress) {
            console.log(`恢复上传: ${savedProgress.uploadedChunks.length}/${savedProgress.totalChunks} 块已完成`);
            this.uploadedChunks = new Set(savedProgress.uploadedChunks);
        }

        // 继续上传...
        for (let i = 0; i < this.totalChunks; i++) {
            if (this.uploadedChunks.has(i)) continue;

            await this.uploadChunk(i);
            this.uploadedChunks.add(i);
            this.saveProgress();  // 每完成一个块就保存
        }

        this.clearProgress();
    }
}
```

localStorage vs IndexedDB:

| 特性 | localStorage | IndexedDB |
|------|-------------|-----------|
| 容量 | 5-10MB | 无限制 (受磁盘限制) |
| 性能 | 同步 API, 阻塞 | 异步 API, 不阻塞 |
| 数据结构 | 字符串键值对 | 结构化对象存储 |
| 适用场景 | 简单状态持久化 | 大量数据或复杂查询 |

建议:
- 小文件上传 (< 100MB, < 50 个块): 使用 localStorage
- 大文件上传 (> 100MB, > 50 个块): 使用 IndexedDB

---

**规则 6: 服务器必须验证块的完整性和顺序**

客户端可能恶意或错误地发送块, 服务器必须验证:

```javascript
// 服务器端块验证
app.post('/upload/chunk', upload.single('file'), async (req, res) => {
    const { fileHash, chunkIndex, totalChunks, fileName } = req.body;
    const chunk = req.file;

    // 验证 1: chunkIndex 必须是有效范围
    const index = parseInt(chunkIndex);
    if (isNaN(index) || index < 0 || index >= parseInt(totalChunks)) {
        return res.status(400).json({
            error: '无效的块索引'
        });
    }

    // 验证 2: 块大小必须合理
    const expectedChunkSize = 2 * 1024 * 1024;  // 2MB
    const maxChunkSize = expectedChunkSize + 1024;  // 允许 1KB 误差

    if (chunk.size > maxChunkSize) {
        return res.status(400).json({
            error: '块大小超出限制'
        });
    }

    // 验证 3: 最后一个块可以小于标准大小
    const isLastChunk = index === parseInt(totalChunks) - 1;
    if (!isLastChunk && chunk.size < expectedChunkSize - 1024) {
        return res.status(400).json({
            error: '块大小不符合预期'
        });
    }

    // 验证 4: 文件哈希格式
    if (!/^[a-f0-9]{64}$/.test(fileHash)) {
        return res.status(400).json({
            error: '无效的文件哈希'
        });
    }

    // 保存块文件
    const chunkDir = path.join(TEMP_DIR, fileHash);
    await fs.mkdir(chunkDir, { recursive: true });

    const chunkPath = path.join(chunkDir, `chunk-${index}`);
    await fs.rename(chunk.path, chunkPath);

    res.json({
        success: true,
        chunkIndex: index
    });
});

// 合并时验证完整性
app.post('/upload/merge', express.json(), async (req, res) => {
    const { fileHash, totalChunks } = req.body;
    const chunkDir = path.join(TEMP_DIR, fileHash);

    // 验证所有块都已上传
    for (let i = 0; i < totalChunks; i++) {
        const chunkPath = path.join(chunkDir, `chunk-${i}`);
        try {
            await fs.access(chunkPath);
        } catch {
            return res.status(400).json({
                error: `块 ${i} 缺失`
            });
        }
    }

    // 合并文件...
});
```

---

**规则 7: 文件合并必须按块顺序进行且支持原子操作**

服务器合并文件时, 必须按照 `chunk-0`, `chunk-1`, `chunk-2` ... 的顺序依次拼接, 保证最终文件正确。同时, 合并过程应该是原子的——要么完全成功, 要么完全失败。

```javascript
// 原子性文件合并
async function mergeChunks(fileHash, fileName, totalChunks) {
    const chunkDir = path.join(TEMP_DIR, fileHash);
    const mergedPath = path.join(MERGED_DIR, fileName);
    const tempMergedPath = `${mergedPath}.tmp`;  // 临时文件

    try {
        // 1. 创建临时合并文件
        const writeStream = fs.createWriteStream(tempMergedPath);

        // 2. 依次写入每个块
        for (let i = 0; i < totalChunks; i++) {
            const chunkPath = path.join(chunkDir, `chunk-${i}`);
            const chunkData = await fs.promises.readFile(chunkPath);

            writeStream.write(chunkData);
        }

        // 3. 关闭流
        writeStream.end();
        await new Promise((resolve, reject) => {
            writeStream.on('finish', resolve);
            writeStream.on('error', reject);
        });

        // 4. 验证合并后文件大小
        const stats = await fs.promises.stat(tempMergedPath);
        const expectedSize = await calculateExpectedSize(chunkDir, totalChunks);

        if (stats.size !== expectedSize) {
            throw new Error(`文件大小不匹配: ${stats.size} vs ${expectedSize}`);
        }

        // 5. 原子性重命名 (临时文件 → 最终文件)
        await fs.promises.rename(tempMergedPath, mergedPath);

        // 6. 删除临时块文件
        await fs.promises.rm(chunkDir, { recursive: true });

        return { success: true, filePath: mergedPath };

    } catch (error) {
        // 清理失败的临时文件
        try {
            await fs.promises.unlink(tempMergedPath);
        } catch {}

        throw error;
    }
}

async function calculateExpectedSize(chunkDir, totalChunks) {
    let totalSize = 0;

    for (let i = 0; i < totalChunks; i++) {
        const chunkPath = path.join(chunkDir, `chunk-${i}`);
        const stats = await fs.promises.stat(chunkPath);
        totalSize += stats.size;
    }

    return totalSize;
}
```

原子性的好处:
- **失败回滚**: 合并失败时, 最终文件不存在, 不会产生损坏的文件
- **并发安全**: 其他进程不会访问到不完整的文件
- **重试友好**: 失败后客户端可以重新请求合并

---

**规则 8: 清理策略避免临时文件占用存储空间**

未完成的上传会在服务器上留下临时块文件, 必须定期清理以避免存储空间耗尽。

```javascript
// 定期清理任务
const cron = require('node-cron');

// 每天凌晨 2 点执行清理
cron.schedule('0 2 * * *', async () => {
    console.log('开始清理过期的临时文件...');

    const now = Date.now();
    const maxAge = 7 * 24 * 60 * 60 * 1000;  // 7 天

    const tempDirs = await fs.promises.readdir(TEMP_DIR);

    for (const dir of tempDirs) {
        const dirPath = path.join(TEMP_DIR, dir);
        const stats = await fs.promises.stat(dirPath);

        // 检查目录修改时间
        const age = now - stats.mtimeMs;

        if (age > maxAge) {
            console.log(`删除过期目录: ${dir} (${Math.floor(age / (24 * 60 * 60 * 1000))} 天)`);
            await fs.promises.rm(dirPath, { recursive: true });
        }
    }

    console.log('清理完成');
});

// 客户端主动清理
async function cancelUpload(fileHash) {
    // 通知服务器删除临时文件
    await fetch('/upload/cancel', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ fileHash })
    });

    // 清理本地状态
    localStorage.removeItem(`upload_${fileHash}`);
}
```

清理策略对比:

| 策略 | 触发时机 | 优点 | 缺点 |
|------|---------|------|------|
| 定时清理 | 每天固定时间 | 自动化, 可靠 | 可能删除正在上传的文件 |
| 按修改时间清理 | 文件超过 7 天未修改 | 精确, 不误删 | 需要定时任务 |
| 客户端主动清理 | 用户取消上传 | 即时释放空间 | 依赖客户端配合 |
| 完成后清理 | 合并成功后 | 及时释放 | 失败的上传无法清理 |

**推荐方案**: 组合策略
- 合并成功后立即删除块文件
- 客户端取消时通知服务器删除
- 定时任务每天清理超过 7 天的临时文件

---

**事故档案编号**: NETWORK-2024-1952
**影响范围**: 文件上传, 断点续传, 分块上传, 状态持久化, 错误重试, 并发控制
**根本原因**: 传统单次上传无法处理网络中断和大文件场景, 需要分块上传 + 文件哈希识别 + 进度持久化实现可恢复上传
**学习成本**: 高 (需理解文件 API、哈希算法、并发控制、错误重试策略、服务器端文件操作)

这是 JavaScript 世界第 152 次被记录的网络与数据事故。可恢复文件上传的核心是文件哈希识别 + 分块上传 + 状态持久化。文件哈希 (SHA-256) 提供跨会话的唯一标识, 采样策略加速大文件哈希计算。分块大小影响上传效率和恢复粒度, 推荐 2-5MB。并发上传需限制并发数 (3-5) 避免浏览器连接池耗尽。错误重试必须使用指数退避 + 随机抖动避免雪崩。localStorage 持久化上传状态支持跨会话恢复。服务器端必须验证块的完整性和顺序, 合并时保证原子性。定期清理临时文件避免存储空间耗尽。理解分块上传的完整生命周期 (哈希计算 → 进度查询 → 块上传 → 合并 → 清理) 是实现可靠大文件上传的基础。

---
