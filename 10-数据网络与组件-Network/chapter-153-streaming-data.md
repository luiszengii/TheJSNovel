《第 153 次记录: 流式传输的技术选型 —— ReadableStream 的渐进式交付》

---

## 技术调研的起点

周三上午九点半, 你打开 Notion 上的技术调研文档。

标题是 "视频平台流式传输方案调研", 创建时间是昨天下午。这是技术总监老李在周二例会上布置的任务: "我们的视频下载功能用户体验很差, 500MB 的视频需要完全下载后才能播放。调研一下流式传输方案, 周五给我一份报告。"

你在白纸上列出了需求:

```
核心需求:
1. 大文件 (500MB+) 的流式传输
2. 边下载边处理 (解码/渲染/保存)
3. 内存占用可控 (不能一次性加载全部数据)
4. 支持取消和暂停
5. 兼容性 (Chrome 85+, Firefox 90+)

技术约束:
- 服务器已支持 Range 请求
- 前端使用 React 18
- 需要支持离线缓存
```

你打开 MDN, 搜索 "stream", 发现了三个核心 API:

```
- ReadableStream: 可读流
- WritableStream: 可写流
- TransformStream: 转换流
```

"看起来 ReadableStream 是关键, " 你在笔记中记录, "但具体怎么用? 和普通的 Fetch 有什么区别?"

---

## Fetch 与 Stream 的对比

你决定从最简单的例子开始。

首先, 你实现了传统的 Fetch 下载方式:

```javascript
// 方式 1: 传统 Fetch (一次性加载)
async function downloadTraditional(url) {
    const startTime = Date.now();
    const startMemory = performance.memory?.usedJSHeapSize || 0;

    const response = await fetch(url);
    const blob = await response.blob();  // ❌ 等待全部数据下载

    const endTime = Date.now();
    const endMemory = performance.memory?.usedJSHeapSize || 0;

    console.log('传统下载统计:');
    console.log(`- 总耗时: ${endTime - startTime}ms`);
    console.log(`- 内存增长: ${((endMemory - startMemory) / 1024 / 1024).toFixed(2)}MB`);
    console.log(`- 文件大小: ${(blob.size / 1024 / 1024).toFixed(2)}MB`);

    return blob;
}
```

你用一个 100MB 的测试视频文件测试, 结果让你皱眉:

```
传统下载统计:
- 总耗时: 4235ms
- 内存增长: 105.3MB
- 文件大小: 102.4MB
- ⚠️ 用户在 4 秒内看到的是 "加载中..." 没有任何进度反馈
```

然后你实现了流式版本:

```javascript
// 方式 2: 流式 Fetch (渐进式处理)
async function downloadStreaming(url, onProgress) {
    const response = await fetch(url);
    const reader = response.body.getReader();  // ✅ 获取 ReadableStream reader

    const contentLength = response.headers.get('Content-Length');
    const total = parseInt(contentLength, 10);

    let received = 0;
    const chunks = [];

    while (true) {
        const { done, value } = await reader.read();  // ✅ 逐块读取

        if (done) {
            break;
        }

        chunks.push(value);
        received += value.length;

        // 实时进度回调
        onProgress({
            received,
            total,
            progress: (received / total) * 100
        });
    }

    // 合并所有块
    const blob = new Blob(chunks);
    return blob;
}
```

测试流式版本:

```javascript
// 测试: 流式下载
const startTime = Date.now();

const blob = await downloadStreaming('/api/videos/sample.mp4', (progress) => {
    console.log(`下载进度: ${progress.progress.toFixed(2)}% (${(progress.received / 1024 / 1024).toFixed(2)}MB / ${(progress.total / 1024 / 1024).toFixed(2)}MB)`);
});

const endTime = Date.now();
console.log(`总耗时: ${endTime - startTime}ms`);
```

控制台输出让你眼前一亮:

```
下载进度: 15.32% (15.7MB / 102.4MB)  ← 832ms 后就有第一次反馈
下载进度: 31.85% (32.6MB / 102.4MB)
下载进度: 48.21% (49.4MB / 102.4MB)
下载进度: 64.93% (66.5MB / 102.4MB)
下载进度: 81.48% (83.4MB / 102.4MB)
下载进度: 98.12% (100.5MB / 102.4MB)
下载进度: 100.00% (102.4MB / 102.4MB)
总耗时: 4187ms  ← 总时间相近, 但用户体验完全不同
```

"关键区别不是总时间, " 你在笔记中写道, "而是用户在第一秒就能看到进度, 而不是傻等 4 秒。"

---

## ReadableStream 的核心机制

你继续深入研究 ReadableStream 的工作原理。

首先, 你实现了一个自定义的 ReadableStream:

```javascript
// 创建自定义 ReadableStream
function createNumberStream(count) {
    let currentNumber = 0;

    return new ReadableStream({
        // start: 流创建时调用
        start(controller) {
            console.log('流已创建');
        },

        // pull: 消费者请求数据时调用
        pull(controller) {
            if (currentNumber < count) {
                // 向流中添加数据
                controller.enqueue(currentNumber);
                console.log(`生成数据: ${currentNumber}`);
                currentNumber++;
            } else {
                // 关闭流
                controller.close();
                console.log('流已关闭');
            }
        },

        // cancel: 消费者取消流时调用
        cancel(reason) {
            console.log('流被取消:', reason);
        }
    });
}
```

你测试这个简单的流:

```javascript
// 测试: 逐个读取数字
async function testNumberStream() {
    const stream = createNumberStream(5);
    const reader = stream.getReader();

    while (true) {
        const { done, value } = await reader.read();

        if (done) {
            console.log('读取完成');
            break;
        }

        console.log(`消费数据: ${value}`);
    }
}

testNumberStream();
```

输出结果让你理解了 ReadableStream 的核心机制:

```
流已创建
生成数据: 0
消费数据: 0
生成数据: 1
消费数据: 1
生成数据: 2
消费数据: 2
生成数据: 3
消费数据: 3
生成数据: 4
消费数据: 4
流已关闭
读取完成
```

"原来是这样, " 你恍然大悟, "ReadableStream 是按需生成数据的。每次调用 `reader.read()`, 才会触发 `pull()` 方法生成新数据。这就是'惰性求值'。"

你画了一个流程图:

```
ReadableStream 工作流程:

1. 创建流 → new ReadableStream({ start, pull, cancel })
2. 获取 reader → stream.getReader()
3. 读取数据 → reader.read() → 触发 pull() → controller.enqueue(data)
4. 消费数据 → { done: false, value: data }
5. 重复步骤 3-4
6. 关闭流 → controller.close() → { done: true }
```

---

## TransformStream 的数据转换

然后你研究了 TransformStream, 发现它可以在数据流经时进行转换。

你实现了一个简单的转换流:

```javascript
// 创建 TransformStream: 将字节流转换为文本
function createTextTransform() {
    const decoder = new TextDecoder();

    return new TransformStream({
        // transform: 每个 chunk 经过时调用
        transform(chunk, controller) {
            // chunk 是 Uint8Array
            const text = decoder.decode(chunk, { stream: true });
            console.log(`解码文本: ${text.substring(0, 50)}...`);

            // 转发给下游
            controller.enqueue(text);
        },

        // flush: 流结束时调用
        flush(controller) {
            console.log('转换完成');
        }
    });
}
```

你用一个实际的场景测试: 下载 JSON 文件并实时解析:

```javascript
// 场景: 流式解析 JSON 行
async function streamParseJSONLines(url) {
    const response = await fetch(url);

    // 构建转换管道: 字节流 → 文本流 → JSON 对象流
    const textStream = response.body
        .pipeThrough(new TextDecoderStream());  // ✅ 浏览器内置的 TransformStream

    const reader = textStream.getReader();
    let buffer = '';

    while (true) {
        const { done, value } = await reader.read();

        if (done) {
            // 处理最后一行
            if (buffer.trim()) {
                const obj = JSON.parse(buffer);
                console.log('解析对象:', obj);
            }
            break;
        }

        buffer += value;

        // 按行分割
        const lines = buffer.split('\n');
        buffer = lines.pop();  // 保留不完整的最后一行

        // 解析完整的行
        for (const line of lines) {
            if (line.trim()) {
                try {
                    const obj = JSON.parse(line);
                    console.log('解析对象:', obj);
                } catch (error) {
                    console.error('解析失败:', line, error);
                }
            }
        }
    }
}
```

你准备了一个测试文件 `data.jsonl` (JSONL 格式: 每行一个 JSON 对象):

```json
{"id": 1, "name": "Alice", "score": 95}
{"id": 2, "name": "Bob", "score": 87}
{"id": 3, "name": "Charlie", "score": 92}
```

测试结果:

```javascript
streamParseJSONLines('/api/data.jsonl');

// 输出 (实时, 不需要等待整个文件下载):
// 解析对象: { id: 1, name: 'Alice', score: 95 }
// 解析对象: { id: 2, name: 'Bob', score: 87 }
// 解析对象: { id: 3, name: 'Charlie', score: 92 }
```

"太强了, " 你感叹, "TransformStream 可以在数据流经时进行转换, 不需要等待全部数据下载完成。"

---

## WritableStream 与持久化

接下来你研究了 WritableStream, 发现它可以将流数据写入目标。

你实现了一个将流数据保存到 IndexedDB 的场景:

```javascript
// 场景: 流式下载并保存到 IndexedDB
async function streamDownloadToIndexedDB(url, filename) {
    const response = await fetch(url);
    const reader = response.body.getReader();

    // 创建 WritableStream 写入 IndexedDB
    const db = await openDatabase();
    const chunks = [];

    const writableStream = new WritableStream({
        // write: 每个 chunk 写入时调用
        write(chunk) {
            console.log(`接收块: ${chunk.length} 字节`);
            chunks.push(chunk);
        },

        // close: 流关闭时调用
        close() {
            console.log('流已关闭, 保存到 IndexedDB...');
            const blob = new Blob(chunks);
            return saveToIndexedDB(db, filename, blob);
        },

        // abort: 流中止时调用
        abort(reason) {
            console.error('流被中止:', reason);
        }
    });

    // 方式 1: 使用 pipeTo
    await response.body.pipeTo(writableStream);

    console.log('文件已保存到 IndexedDB');
}

// IndexedDB 操作
async function openDatabase() {
    return new Promise((resolve, reject) => {
        const request = indexedDB.open('FileCache', 1);

        request.onupgradeneeded = (e) => {
            const db = e.target.result;
            if (!db.objectStoreNames.contains('files')) {
                db.createObjectStore('files', { keyPath: 'filename' });
            }
        };

        request.onsuccess = (e) => resolve(e.target.result);
        request.onerror = (e) => reject(e.target.error);
    });
}

async function saveToIndexedDB(db, filename, blob) {
    return new Promise((resolve, reject) => {
        const tx = db.transaction('files', 'readwrite');
        const store = tx.objectStore('files');

        const request = store.put({
            filename,
            blob,
            timestamp: Date.now()
        });

        request.onsuccess = () => resolve();
        request.onerror = (e) => reject(e.target.error);
    });
}
```

你测试这个实现:

```javascript
// 测试: 下载并缓存
await streamDownloadToIndexedDB('/api/videos/sample.mp4', 'sample.mp4');

// 输出:
// 接收块: 65536 字节
// 接收块: 65536 字节
// 接收块: 65536 字节
// ...
// 流已关闭, 保存到 IndexedDB...
// 文件已保存到 IndexedDB
```

然后你验证数据已成功保存:

```javascript
// 验证: 从 IndexedDB 读取
async function loadFromIndexedDB(filename) {
    const db = await openDatabase();
    const tx = db.transaction('files', 'readonly');
    const store = tx.objectStore('files');

    return new Promise((resolve, reject) => {
        const request = store.get(filename);

        request.onsuccess = (e) => {
            const record = e.target.result;
            if (record) {
                console.log('找到缓存文件:');
                console.log(`- 文件名: ${record.filename}`);
                console.log(`- 大小: ${(record.blob.size / 1024 / 1024).toFixed(2)}MB`);
                console.log(`- 缓存时间: ${new Date(record.timestamp).toLocaleString()}`);
                resolve(record.blob);
            } else {
                resolve(null);
            }
        };

        request.onerror = (e) => reject(e.target.error);
    });
}

const cachedBlob = await loadFromIndexedDB('sample.mp4');
// 输出:
// 找到缓存文件:
// - 文件名: sample.mp4
// - 大小: 102.43MB
// - 缓存时间: 2024-01-17 10:23:45
```

---

## 完整的流式视频播放方案

你整合了所有研究成果, 实现了一个完整的流式视频播放方案:

```javascript
// 完整方案: 流式下载 + 实时播放 + 离线缓存
class StreamingVideoPlayer {
    constructor(videoElement, options = {}) {
        this.video = videoElement;
        this.cacheName = options.cacheName || 'video-cache';
        this.chunkSize = options.chunkSize || 1024 * 1024;  // 1MB
    }

    // 播放 (优先使用缓存)
    async play(url) {
        // 1. 尝试从缓存加载
        const cachedBlob = await this.loadFromCache(url);
        if (cachedBlob) {
            console.log('使用缓存播放');
            this.video.src = URL.createObjectURL(cachedBlob);
            return;
        }

        // 2. 流式下载并播放
        console.log('流式下载并播放');
        await this.streamPlay(url);
    }

    // 流式播放
    async streamPlay(url) {
        const response = await fetch(url);
        const contentLength = response.headers.get('Content-Length');
        const total = parseInt(contentLength, 10);

        let received = 0;
        const chunks = [];

        const reader = response.body.getReader();

        // 创建 MediaSource
        const mediaSource = new MediaSource();
        this.video.src = URL.createObjectURL(mediaSource);

        await new Promise((resolve) => {
            mediaSource.addEventListener('sourceopen', resolve, { once: true });
        });

        const sourceBuffer = mediaSource.addSourceBuffer('video/mp4; codecs="avc1.42E01E, mp4a.40.2"');

        // 读取流并喂给 SourceBuffer
        const appendChunk = async (chunk) => {
            return new Promise((resolve) => {
                sourceBuffer.appendBuffer(chunk);
                sourceBuffer.addEventListener('updateend', resolve, { once: true });
            });
        };

        while (true) {
            const { done, value } = await reader.read();

            if (done) {
                break;
            }

            chunks.push(value);
            received += value.length;

            // 实时喂数据给 SourceBuffer
            await appendChunk(value);

            // 更新进度
            const progress = (received / total) * 100;
            console.log(`缓冲进度: ${progress.toFixed(2)}%`);

            // 当有足够缓冲时, 开始播放
            if (progress > 10 && this.video.paused) {
                this.video.play();
                console.log('开始播放 (已缓冲 10%)');
            }
        }

        // 结束流
        mediaSource.endOfStream();

        // 保存到缓存
        const blob = new Blob(chunks);
        await this.saveToCache(url, blob);
        console.log('已保存到缓存');
    }

    // 保存到 IndexedDB
    async saveToCache(url, blob) {
        const db = await openDatabase();
        return saveToIndexedDB(db, url, blob);
    }

    // 从 IndexedDB 加载
    async loadFromCache(url) {
        const db = await openDatabase();
        return loadFromIndexedDB(url);
    }
}
```

你创建测试页面:

```html
<!DOCTYPE html>
<html>
<head>
    <title>流式视频播放测试</title>
</head>
<body>
    <video id="video" controls width="800"></video>
    <div id="stats"></div>

    <script type="module">
        const video = document.querySelector('#video');
        const stats = document.querySelector('#stats');

        const player = new StreamingVideoPlayer(video);

        // 播放视频
        await player.play('/api/videos/sample.mp4');

        // 监控播放状态
        video.addEventListener('progress', () => {
            const buffered = video.buffered;
            if (buffered.length > 0) {
                const bufferedEnd = buffered.end(buffered.length - 1);
                const duration = video.duration;
                const percent = (bufferedEnd / duration) * 100;

                stats.textContent = `缓冲进度: ${percent.toFixed(2)}% | 播放位置: ${video.currentTime.toFixed(2)}s`;
            }
        });

        video.addEventListener('playing', () => {
            console.log('视频开始播放');
        });

        video.addEventListener('waiting', () => {
            console.log('等待缓冲...');
        });
    </script>
</body>
</html>
```

测试结果让你非常满意:

```
流式下载并播放
缓冲进度: 12.34%
开始播放 (已缓冲 10%)  ← 用户在 1.2 秒后就能开始观看
缓冲进度: 25.67%
缓冲进度: 38.92%
缓冲进度: 52.18%
缓冲进度: 65.43%
缓冲进度: 78.69%
缓冲进度: 91.94%
缓冲进度: 100.00%
已保存到缓存
```

---

## Backpressure 与流量控制

在测试过程中, 你遇到了一个性能问题: 当下载速度很快时, 内存占用会快速增长。

你研究发现这是因为缺少 "背压 (backpressure)" 机制——生产者生成数据的速度超过了消费者处理的速度。

你实现了一个支持背压的流:

```javascript
// 支持背压的 ReadableStream
function createBackpressureStream(dataSource) {
    let index = 0;

    return new ReadableStream({
        async pull(controller) {
            // pull 只在下游准备好时才被调用
            if (index < dataSource.length) {
                const data = dataSource[index];
                index++;

                // 模拟异步数据生成
                await new Promise(resolve => setTimeout(resolve, 10));

                controller.enqueue(data);
                console.log(`生成数据 ${index}: ${data} (下游已准备好)`);
            } else {
                controller.close();
            }
        }
    }, {
        // 队列策略: 限制缓冲区大小
        highWaterMark: 2,  // 最多缓冲 2 个 chunk
        size(chunk) {
            return 1;  // 每个 chunk 计为 1 个单位
        }
    });
}
```

你对比测试有无背压控制的差异:

```javascript
// 测试 1: 无背压控制 (默认)
async function testWithoutBackpressure() {
    console.log('=== 测试: 无背压控制 ===');

    const stream = new ReadableStream({
        start(controller) {
            // 一次性生成所有数据
            for (let i = 0; i < 100; i++) {
                controller.enqueue(i);
                console.log(`生成数据: ${i}`);
            }
            controller.close();
        }
    });

    const reader = stream.getReader();

    for (let i = 0; i < 10; i++) {
        const { value } = await reader.read();
        console.log(`消费数据: ${value}`);
        await new Promise(resolve => setTimeout(resolve, 100));  // 模拟慢速消费
    }
}

await testWithoutBackpressure();

// 输出:
// 生成数据: 0
// 生成数据: 1
// ...
// 生成数据: 99  ← 所有数据立即生成, 堆积在内存中
// 消费数据: 0
// (100ms 延迟)
// 消费数据: 1
// (100ms 延迟)
// ...
```

```javascript
// 测试 2: 有背压控制
async function testWithBackpressure() {
    console.log('=== 测试: 有背压控制 ===');

    const data = Array.from({ length: 100 }, (_, i) => i);
    const stream = createBackpressureStream(data);

    const reader = stream.getReader();

    for (let i = 0; i < 10; i++) {
        const { value } = await reader.read();
        console.log(`消费数据: ${value}`);
        await new Promise(resolve => setTimeout(resolve, 100));  // 模拟慢速消费
    }
}

await testWithBackpressure();

// 输出:
// 生成数据 1: 0 (下游已准备好)
// 消费数据: 0
// (100ms 延迟)
// 生成数据 2: 1 (下游已准备好)
// 消费数据: 1
// (100ms 延迟)
// 生成数据 3: 2 (下游已准备好)
// ...
// ✅ 数据按需生成, 不会堆积
```

"原来如此, " 你理解了背压机制, "ReadableStream 的 `pull()` 方法只在下游准备好时才被调用, 这就是自动的流量控制。"

---

## 实战场景: 大文件分块上传

你想到了一个实际应用场景: 使用流将大文件分块上传。

你实现了一个流式上传方案:

```javascript
// 场景: 流式分块上传
class StreamingUploader {
    constructor(file, options = {}) {
        this.file = file;
        this.chunkSize = options.chunkSize || 1024 * 1024 * 2;  // 2MB
        this.totalChunks = Math.ceil(file.size / this.chunkSize);
    }

    // 创建文件读取流
    createFileStream() {
        let offset = 0;
        const file = this.file;
        const chunkSize = this.chunkSize;

        return new ReadableStream({
            async pull(controller) {
                if (offset >= file.size) {
                    controller.close();
                    return;
                }

                const end = Math.min(offset + chunkSize, file.size);
                const chunk = file.slice(offset, end);
                const buffer = await chunk.arrayBuffer();

                controller.enqueue({
                    index: Math.floor(offset / chunkSize),
                    data: new Uint8Array(buffer),
                    offset,
                    size: end - offset
                });

                offset = end;
            }
        });
    }

    // 创建上传转换流
    createUploadTransform(uploadUrl, fileHash) {
        return new TransformStream({
            async transform(chunk, controller) {
                // 上传单个块
                const formData = new FormData();
                formData.append('file', new Blob([chunk.data]));
                formData.append('fileHash', fileHash);
                formData.append('chunkIndex', chunk.index);
                formData.append('totalChunks', this.totalChunks);

                try {
                    const response = await fetch(uploadUrl, {
                        method: 'POST',
                        body: formData
                    });

                    if (!response.ok) {
                        throw new Error(`上传块 ${chunk.index} 失败: HTTP ${response.status}`);
                    }

                    console.log(`块 ${chunk.index} 上传成功 (${chunk.size} 字节)`);

                    // 转发上传结果
                    controller.enqueue({
                        index: chunk.index,
                        success: true,
                        size: chunk.size
                    });

                } catch (error) {
                    console.error(`块 ${chunk.index} 上传失败:`, error);

                    controller.enqueue({
                        index: chunk.index,
                        success: false,
                        error: error.message
                    });
                }
            }
        });
    }

    // 执行流式上传
    async upload(uploadUrl, fileHash, onProgress) {
        const fileStream = this.createFileStream();
        const uploadTransform = this.createUploadTransform(uploadUrl, fileHash);

        // 创建统计 WritableStream
        let uploadedChunks = 0;
        let uploadedBytes = 0;

        const statsStream = new WritableStream({
            write(result) {
                if (result.success) {
                    uploadedChunks++;
                    uploadedBytes += result.size;

                    onProgress({
                        uploadedChunks,
                        totalChunks: this.totalChunks,
                        uploadedBytes,
                        totalBytes: this.file.size,
                        progress: (uploadedChunks / this.totalChunks) * 100
                    });
                }
            },

            close() {
                console.log('所有块上传完成');
            },

            abort(reason) {
                console.error('上传被中止:', reason);
            }
        });

        // 构建流管道: 文件读取 → 上传转换 → 统计
        await fileStream
            .pipeThrough(uploadTransform)
            .pipeTo(statsStream);
    }
}
```

你测试这个流式上传实现:

```javascript
// 测试: 上传 100MB 文件
const fileInput = document.querySelector('#file');
fileInput.addEventListener('change', async (e) => {
    const file = e.target.files[0];
    console.log(`选择文件: ${file.name} (${(file.size / 1024 / 1024).toFixed(2)}MB)`);

    const uploader = new StreamingUploader(file, {
        chunkSize: 1024 * 1024 * 2  // 2MB
    });

    const fileHash = await calculateFileHash(file);  // 计算文件哈希

    await uploader.upload('/api/upload/chunk', fileHash, (progress) => {
        console.log(`上传进度: ${progress.progress.toFixed(2)}% (${progress.uploadedChunks}/${progress.totalChunks} 块)`);
    });

    console.log('文件上传完成');
});
```

测试结果:

```
选择文件: video.mp4 (102.43MB)
计算文件哈希: a3f5b8c2d9e1f4a7...
块 0 上传成功 (2097152 字节)
上传进度: 2.00% (1/50 块)
块 1 上传成功 (2097152 字节)
上传进度: 4.00% (2/50 块)
块 2 上传成功 (2097152 字节)
上传进度: 6.00% (3/50 块)
...
块 49 上传成功 (485376 字节)
上传进度: 100.00% (50/50 块)
所有块上传完成
文件上传完成
```

"太优雅了, " 你感叹, "流式上传让代码变得非常清晰: 读取流 → 转换流 → 写入流, 就像水管一样。"

---

## 调研报告与最佳实践

周五上午, 你整理好了完整的技术调研报告。

你在 Notion 中创建了一个新页面, 标题是 "Streaming API 技术选型报告", 包含以下内容:

**核心结论**:

1. **推荐方案**: 使用 ReadableStream + TransformStream + WritableStream 构建流式处理管道
2. **适用场景**: 大文件下载/上传、实时数据处理、视频流播放、日志分析
3. **性能优势**: 内存占用可控、首字节时间短、支持取消和暂停
4. **兼容性**: Chrome 85+, Firefox 90+, Safari 14.1+, Edge 85+

**技术方案对比**:

| 方案 | 优点 | 缺点 | 适用场景 |
|------|------|------|----------|
| 传统 Fetch + Blob | 简单直观 | 内存占用高, 无进度反馈 | 小文件 (<10MB) |
| ReadableStream | 渐进式交付, 内存可控 | API 复杂度较高 | 大文件, 实时流 |
| MediaSource API | 视频边下边播 | 仅支持媒体文件 | 视频/音频流 |
| WebRTC Data Channel | 点对点传输 | 需要信令服务器 | 实时通信 |

**实施建议**:

1. **视频播放**: 使用 ReadableStream + MediaSource API, 支持流式播放和离线缓存
2. **文件上传**: 使用流式分块上传, 支持断点续传和并发控制
3. **数据处理**: 使用 TransformStream 构建数据转换管道
4. **日志分析**: 使用流式 JSON 解析, 逐行处理大文件

**风险评估**:

1. **浏览器兼容性**: Safari 14.1+ 才支持, 需要 polyfill 或降级方案
2. **学习成本**: API 较复杂, 团队需要学习流式编程思维
3. **调试难度**: 流式代码的调试比传统代码困难
4. **错误处理**: 需要处理流中断、网络错误、背压等复杂情况

**代码示例**: (附上完整的 StreamingVideoPlayer 和 StreamingUploader 实现)

你点击 "发送给老李", 附上一句话: "周五上午完成, 建议采用 ReadableStream 方案, 已包含完整实现代码。"

---

## 知识档案: Streaming API 的八大核心机制

**规则 1: ReadableStream 是惰性的按需生产者**

ReadableStream 不会一次性生成所有数据, 而是在消费者调用 `reader.read()` 时才触发 `pull()` 方法生成新数据。

```javascript
// ReadableStream 工作机制
const stream = new ReadableStream({
    // start: 流创建时调用一次
    start(controller) {
        console.log('流已创建');
    },

    // pull: 消费者请求数据时调用
    pull(controller) {
        // 生成数据
        const data = generateData();
        controller.enqueue(data);  // 将数据推入流
    },

    // cancel: 消费者取消流时调用
    cancel(reason) {
        console.log('流被取消:', reason);
    }
});

// 消费流
const reader = stream.getReader();
const { done, value } = await reader.read();  // 触发 pull()
```

为什么是惰性的:
- **内存效率**: 不需要一次性加载全部数据到内存
- **按需生成**: 只在需要时生成数据, 避免浪费
- **自然背压**: 消费者控制生产速度, 防止数据堆积

---

**规则 2: `response.body` 是 ReadableStream 实例**

Fetch API 返回的 `response.body` 是一个 ReadableStream, 可以逐块读取响应数据。

```javascript
// 传统方式: 等待整个响应
const response = await fetch('/api/data');
const blob = await response.blob();  // ❌ 阻塞直到全部下载

// 流式方式: 逐块读取
const response = await fetch('/api/data');
const reader = response.body.getReader();  // ✅ 获取 ReadableStream reader

while (true) {
    const { done, value } = await reader.read();

    if (done) break;

    // value 是 Uint8Array, 包含部分响应数据
    console.log(`接收 ${value.length} 字节`);
}
```

对比:

| 方式 | 首字节时间 | 内存占用 | 进度反馈 |
|------|------------|----------|----------|
| response.blob() | 等待全部下载 | 完整文件大小 | 无 |
| response.body.getReader() | 立即开始 | 单个 chunk 大小 | 实时 |

---

**规则 3: TransformStream 在数据流经时转换数据**

TransformStream 位于 ReadableStream 和 WritableStream 之间, 对数据进行转换。

```javascript
// TransformStream 结构
const transformStream = new TransformStream({
    // transform: 每个 chunk 经过时调用
    transform(chunk, controller) {
        // 转换数据
        const transformed = processChunk(chunk);

        // 转发给下游
        controller.enqueue(transformed);
    },

    // flush: 流结束时调用 (可选)
    flush(controller) {
        // 处理最后的数据
        controller.enqueue(finalData);
    }
});

// 使用 pipeThrough 连接流
const transformed = readableStream
    .pipeThrough(transformStream)  // 经过转换
    .pipeThrough(anotherTransform);  // 可以链式连接多个转换
```

内置 TransformStream:
- `TextDecoderStream`: 字节流 → 文本流
- `TextEncoderStream`: 文本流 → 字节流
- `CompressionStream`: 原始数据 → 压缩数据
- `DecompressionStream`: 压缩数据 → 原始数据

---

**规则 4: WritableStream 是数据的最终目标**

WritableStream 接收数据并执行副作用 (写文件、网络发送、显示等)。

```javascript
// WritableStream 结构
const writableStream = new WritableStream({
    // write: 每次写入数据时调用
    write(chunk) {
        // 处理数据 (保存、发送、显示等)
        console.log('接收数据:', chunk);
    },

    // close: 流正常关闭时调用
    close() {
        console.log('流已关闭');
    },

    // abort: 流异常中止时调用
    abort(reason) {
        console.error('流被中止:', reason);
    }
});

// 使用 pipeTo 连接流
await readableStream.pipeTo(writableStream);
```

WritableStream 的用途:
- 保存到文件系统 (File System Access API)
- 保存到 IndexedDB
- 发送到网络 (Fetch upload)
- 更新 UI (逐行显示日志)

---

**规则 5: `pipeThrough` 和 `pipeTo` 构建流管道**

流管道通过 `pipeThrough` 和 `pipeTo` 连接, 形成数据处理链。

```javascript
// 完整的流管道
await readableStream
    .pipeThrough(transformStream1)  // 转换 1
    .pipeThrough(transformStream2)  // 转换 2
    .pipeTo(writableStream);        // 最终目标

// 等价于:
const stream1 = readableStream.pipeThrough(transformStream1);
const stream2 = stream1.pipeThrough(transformStream2);
await stream2.pipeTo(writableStream);
```

管道的特性:
- **自动背压**: 下游慢会自动减慢上游
- **错误传播**: 任一环节错误会传播到整个管道
- **取消传播**: 取消下游会自动取消上游
- **链式调用**: 可以无限链接转换流

典型管道模式:

```javascript
// 模式 1: 下载 → 解压 → 解码 → 保存
await fetch(url).body
    .pipeThrough(new DecompressionStream('gzip'))
    .pipeThrough(new TextDecoderStream())
    .pipeTo(fileWritableStream);

// 模式 2: 读取 → 压缩 → 上传
await fileReadableStream
    .pipeThrough(new CompressionStream('gzip'))
    .pipeTo(uploadWritableStream);

// 模式 3: 下载 → 转换 → 显示 + 保存
const teeStreams = response.body.tee();  // 分叉流

teeStreams[0].pipeTo(displayStream);  // 显示
teeStreams[1].pipeTo(cacheStream);    // 缓存
```

---

**规则 6: Backpressure 自动调节生产和消费速度**

背压 (backpressure) 是流式系统的自动流量控制机制, 防止数据堆积。

```javascript
// 背压工作原理
const stream = new ReadableStream({
    pull(controller) {
        // ✅ pull 只在下游准备好时才被调用
        console.log('下游准备好了, 生成新数据');
        controller.enqueue(data);
    }
}, {
    // 队列策略: 控制缓冲区大小
    highWaterMark: 2,  // 最多缓冲 2 个 chunk
    size(chunk) {
        return chunk.byteLength;  // 按字节计算大小
    }
});
```

背压的三个层次:

**1. 内部队列控制**:
```javascript
// highWaterMark 控制内部缓冲区
new ReadableStream({
    pull(controller) {
        // 当内部队列 < highWaterMark 时才调用
    }
}, {
    highWaterMark: 5  // 队列最多 5 个 chunk
});
```

**2. pipeTo 自动背压**:
```javascript
// pipeTo 会自动协调上下游速度
await readableStream.pipeTo(writableStream);
// ✅ 如果 writableStream 慢, readableStream 会自动减速
```

**3. 手动背压控制**:
```javascript
const reader = stream.getReader();

while (true) {
    const { done, value } = await reader.read();

    if (done) break;

    // 处理数据 (如果慢, 会自动减慢上游)
    await slowProcessing(value);
}
```

背压的好处:
- **内存可控**: 防止快速生产导致内存爆炸
- **自动平衡**: 无需手动协调速度
- **系统稳定**: 避免级联失败

---

**规则 7: `tee()` 分叉流实现一份数据多次消费**

`tee()` 方法将一个 ReadableStream 分叉为两个独立的流, 可以分别消费。

```javascript
// 分叉流
const response = await fetch('/api/data');
const [stream1, stream2] = response.body.tee();

// stream1 和 stream2 独立消费相同的数据
stream1.pipeTo(displayStream);   // 用途 1: 显示
stream2.pipeTo(cacheStream);     // 用途 2: 缓存
```

分叉的特性:
- **独立读取**: 两个流可以独立读取, 互不影响
- **数据复制**: 数据会被复制给两个流
- **背压协调**: 两个流的背压会同步到原始流

典型应用场景:

```javascript
// 场景 1: 下载 + 缓存
async function downloadAndCache(url) {
    const response = await fetch(url);
    const [displayStream, cacheStream] = response.body.tee();

    // 同时进行显示和缓存
    await Promise.all([
        displayStream.pipeTo(createDisplaySink()),
        cacheStream.pipeTo(createCacheSink())
    ]);
}

// 场景 2: 进度追踪
async function downloadWithProgress(url, onProgress) {
    const response = await fetch(url);
    const [dataStream, progressStream] = response.body.tee();

    // 一个流用于数据处理
    const dataPromise = dataStream.pipeTo(dataSink);

    // 另一个流用于进度追踪
    const progressPromise = (async () => {
        const reader = progressStream.getReader();
        let received = 0;

        while (true) {
            const { done, value } = await reader.read();
            if (done) break;

            received += value.length;
            onProgress(received);
        }
    })();

    await Promise.all([dataPromise, progressPromise]);
}
```

**⚠️ 注意**: 分叉会增加内存占用, 因为数据需要复制给两个流。

---

**规则 8: 错误处理和流取消需要显式管理**

流式操作的错误处理比传统代码复杂, 需要处理多个环节的错误。

```javascript
// 完整的错误处理
async function robustStreamProcessing(url) {
    let reader;

    try {
        const response = await fetch(url);

        if (!response.ok) {
            throw new Error(`HTTP ${response.status}`);
        }

        reader = response.body.getReader();

        while (true) {
            const { done, value } = await reader.read();

            if (done) break;

            // 处理数据
            try {
                await processChunk(value);
            } catch (error) {
                console.error('处理块失败:', error);
                // 可以选择继续或中止
                break;
            }
        }

    } catch (error) {
        console.error('流处理失败:', error);

    } finally {
        // ✅ 必须释放 reader
        if (reader) {
            reader.releaseLock();
        }
    }
}
```

流取消:

```javascript
// 主动取消流
const controller = new AbortController();
const signal = controller.signal;

const response = await fetch(url, { signal });
const reader = response.body.getReader();

// 用户取消操作
cancelButton.addEventListener('click', () => {
    controller.abort();  // 取消 fetch
    reader.cancel('用户取消');  // 取消流读取
});

// 处理取消
try {
    while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        // 处理数据...
    }
} catch (error) {
    if (error.name === 'AbortError') {
        console.log('操作已取消');
    } else {
        throw error;
    }
}
```

管道错误处理:

```javascript
// pipeTo 的错误处理
try {
    await readableStream.pipeTo(writableStream, {
        preventClose: false,   // 源流关闭时关闭目标流
        preventAbort: false,   // 源流中止时中止目标流
        preventCancel: false,  // 目标流中止时取消源流
        signal: abortSignal    // AbortSignal 用于外部取消
    });
} catch (error) {
    console.error('管道失败:', error);
}
```

错误处理的关键点:
- **reader.releaseLock()**: 必须释放 reader 锁, 否则流无法被其他消费者使用
- **reader.cancel()**: 主动取消流时调用
- **try-finally**: 确保资源释放
- **AbortController**: 用于外部取消控制

---

**事故档案编号**: NETWORK-2024-1953
**影响范围**: ReadableStream, WritableStream, TransformStream, 流式数据处理, 背压控制
**根本原因**: 传统 Fetch 方式一次性加载全部数据, 导致内存占用高、无进度反馈、用户体验差
**学习成本**: 高 (需理解流式编程思维和背压机制)

这是 JavaScript 世界第 153 次被记录的网络与数据事故。Streaming API 提供了 ReadableStream, WritableStream, TransformStream 三种核心流类型, 构建数据处理管道。ReadableStream 是惰性的按需生产者, 只在消费者请求时才生成数据。`response.body` 是 ReadableStream 实例, 可以逐块读取响应数据。TransformStream 在数据流经时转换数据, 可以链式连接多个转换。WritableStream 是数据的最终目标, 执行副作用操作。`pipeThrough` 和 `pipeTo` 构建流管道, 自动处理背压和错误传播。Backpressure 自动调节生产和消费速度, 防止数据堆积导致内存爆炸。`tee()` 方法分叉流实现一份数据多次消费。错误处理需要显式管理 reader 锁释放和流取消。理解流式编程思维和背压机制是构建高性能数据处理系统的关键。

---
