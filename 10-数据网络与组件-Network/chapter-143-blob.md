《第 143 次记录: 文件上传的性能陷阱 —— Blob 的不可变真相》

---

## 监控告警

周一上午十点半，你的手机震动了三次。

Slack 上的 #alerts 频道弹出了红色的 @channel 标记："文件上传服务内存占用异常，已达 85%，请立即检查。"

你放下手中的咖啡，快速打开监控面板。图表上的内存使用曲线像一条陡峭的山脉，从周五下午开始就一路攀升，现在已经逼近了服务器的内存上限。

"这不对劲，" 你皱眉，"上周刚上线的图片压缩功能应该会降低内存占用才对，为什么反而暴增了？"

你点开详细日志，发现最频繁的操作是用户上传大图片时的压缩处理。每次用户上传一个 5MB 的照片，服务器内存就会瞬间增加 15-20MB，而且这些内存在处理完成后并没有立即释放。

更诡异的是，当多个用户同时上传文件时，内存占用会呈指数级增长。周五下午恰好是用户活跃高峰期，整个系统差点就崩溃了。

"必须今天找到根因，" 你想，"否则下个周末就会真的出事。"

---

## 代码追踪

周一下午两点，你调出了上周上线的压缩功能代码。

这是你的同事小陈写的，逻辑看起来很清晰：用户上传图片 → 读取文件 → 压缩处理 → 生成新文件 → 上传到云存储。

```javascript
async function compressImage(file) {
    // 读取原始文件
    const reader = new FileReader();
    reader.readAsDataURL(file);

    return new Promise((resolve) => {
        reader.onload = async (e) => {
            const img = new Image();
            img.src = e.target.result;

            img.onload = () => {
                // 压缩处理
                const canvas = document.createElement('canvas');
                const ctx = canvas.getContext('2d');

                canvas.width = img.width * 0.8;
                canvas.height = img.height * 0.8;
                ctx.drawImage(img, 0, 0, canvas.width, canvas.height);

                // 生成压缩后的数据
                canvas.toBlob((blob) => {
                    // 转换成新的File对象
                    const compressedFile = new File([blob], file.name, {
                        type: 'image/jpeg',
                        lastModified: Date.now()
                    });

                    resolve(compressedFile);
                }, 'image/jpeg', 0.8);
            };
        };
    });
}
```

"代码逻辑没问题啊，" 你自言自语，"为什么会导致内存泄漏？"

你决定在本地环境复现问题。你准备了一个 5MB 的测试图片，打开 Chrome DevTools 的 Performance 面板，开始录制内存快照。

第一次上传：内存占用从 50MB 跳到 75MB。

第二次上传：内存占用从 75MB 跳到 100MB。

第三次上传：内存占用从 100MB 跳到 125MB。

"等等..." 你盯着内存曲线，"每次上传后，内存都没有回到初始值。这说明有对象没有被垃圾回收！"

你点开 Memory 面板，拍了一个堆快照。在快照中，你看到了大量的 `Blob` 和 `File` 对象，它们占据了大部分内存空间。

"原来问题出在这里，" 你恍然，"但 Blob 和 File 不是应该会被自动回收的吗？"

---

## 深入调查

周二上午九点，你开始系统地研究 Blob 对象的特性。

你首先测试了 Blob 的基本行为：

```javascript
// 创建一个简单的 Blob
const blob1 = new Blob(['Hello World'], { type: 'text/plain' });
console.log(blob1.size);  // 11
console.log(blob1.type);  // 'text/plain'

// 尝试修改 Blob
blob1.size = 100;  // 无效
console.log(blob1.size);  // 仍然是 11

// Blob 是不可变的
const blob2 = new Blob(['Hello']);
const blob3 = new Blob([blob2, ' World']);
console.log(blob2.size);  // 5 (没有改变)
console.log(blob3.size);  // 11
```

"Blob 是不可变的，" 你意识到，"这意味着每次调用 `canvas.toBlob()` 都会创建一个新的 Blob 对象。"

你又测试了 File 对象的特性：

```javascript
const file = new File([blob1], 'test.txt', {
    type: 'text/plain',
    lastModified: Date.now()
});

console.log(file instanceof Blob);  // true
console.log(file instanceof File);  // true
console.log(file.name);  // 'test.txt'
console.log(file.size);  // 11
```

"File 继承自 Blob，" 你总结，"所以 File 也是不可变的。"

但这还不能解释为什么会内存泄漏。你继续深入调查，查看了 MDN 文档中关于 Blob 的内存管理部分。文档中提到了一个关键概念——**Blob URL**。

你突然想起，压缩功能中还有一个预览功能，会为压缩后的图片生成预览 URL：

```javascript
// 在压缩代码后面，还有这段预览逻辑
const previewUrl = URL.createObjectURL(compressedFile);
document.querySelector('#preview').src = previewUrl;
```

"这就是问题所在！" 你兴奋地说，"URL.createObjectURL() 创建的 URL 会持有 Blob 的引用，导致 Blob 无法被垃圾回收！"

你在控制台验证了这个假设：

```javascript
// 创建 Blob URL
const blob = new Blob(['test'], { type: 'text/plain' });
const url = URL.createObjectURL(blob);
console.log(url);  // blob:http://localhost:3000/abc123...

// Blob URL 会持有 Blob 的引用
// 即使没有其他引用，Blob 也不会被回收
blob = null;  // 无效，因为 url 仍然引用着 Blob
```

---

## 性能分析

周二下午三点，你开始量化内存泄漏的程度。

你写了一个测试脚本，模拟用户连续上传 10 张图片：

```javascript
async function testMemoryLeak() {
    const initialMemory = performance.memory.usedJSHeapSize;

    for (let i = 0; i < 10; i++) {
        const file = await createTestImage();  // 创建一个 5MB 的测试图片
        const compressed = await compressImage(file);

        // 生成预览 URL (旧代码)
        const url = URL.createObjectURL(compressed);
        document.querySelector('#preview').src = url;

        await sleep(100);  // 模拟用户操作间隔
    }

    const finalMemory = performance.memory.usedJSHeapSize;
    const leakedMemory = finalMemory - initialMemory;

    console.log('初始内存:', (initialMemory / 1024 / 1024).toFixed(2), 'MB');
    console.log('最终内存:', (finalMemory / 1024 / 1024).toFixed(2), 'MB');
    console.log('泄漏内存:', (leakedMemory / 1024 / 1024).toFixed(2), 'MB');
}

testMemoryLeak();
```

测试结果让你倒吸一口凉气：

```
初始内存: 52.34 MB
最终内存: 127.89 MB
泄漏内存: 75.55 MB
```

"10 张图片就泄漏了 75MB 内存，" 你算了一下，"如果 100 个用户同时上传，那就是 7.5GB！难怪服务器内存会爆掉。"

你又测试了正确的做法——手动释放 Blob URL：

```javascript
async function testMemoryFixed() {
    const initialMemory = performance.memory.usedJSHeapSize;

    for (let i = 0; i < 10; i++) {
        const file = await createTestImage();
        const compressed = await compressImage(file);

        // 生成预览 URL
        const url = URL.createObjectURL(compressed);
        document.querySelector('#preview').src = url;

        // ✅ 关键：释放 URL
        URL.revokeObjectURL(url);

        await sleep(100);
    }

    const finalMemory = performance.memory.usedJSHeapSize;
    const leakedMemory = finalMemory - initialMemory;

    console.log('泄漏内存:', (leakedMemory / 1024 / 1024).toFixed(2), 'MB');
}
```

这次的结果让你满意：

```
泄漏内存: 3.21 MB
```

"从 75MB 降到 3MB，" 你点头，"内存泄漏几乎完全消除了。"

---

## 修复方案

周三上午十点，你开始重构压缩功能的代码。

你首先修改了 `compressImage` 函数，添加了 Blob URL 的生命周期管理：

```javascript
// ❌ 旧代码：URL 泄漏
async function compressImageOld(file) {
    // ... 压缩逻辑

    canvas.toBlob((blob) => {
        const compressedFile = new File([blob], file.name, {
            type: 'image/jpeg',
            lastModified: Date.now()
        });

        // 生成预览 URL，但从未释放
        const url = URL.createObjectURL(compressedFile);
        document.querySelector('#preview').src = url;

        resolve(compressedFile);
    }, 'image/jpeg', 0.8);
}

// ✅ 新代码：正确管理 URL 生命周期
async function compressImageNew(file) {
    // ... 压缩逻辑

    canvas.toBlob((blob) => {
        const compressedFile = new File([blob], file.name, {
            type: 'image/jpeg',
            lastModified: Date.now()
        });

        // 生成预览 URL
        const url = URL.createObjectURL(compressedFile);
        const previewImg = document.querySelector('#preview');

        // 清理旧 URL
        if (previewImg.src && previewImg.src.startsWith('blob:')) {
            URL.revokeObjectURL(previewImg.src);
        }

        previewImg.src = url;

        // 图片加载完成后释放 URL
        previewImg.onload = () => {
            URL.revokeObjectURL(url);
        };

        resolve(compressedFile);
    }, 'image/jpeg', 0.8);
}
```

你又创建了一个工具类，统一管理 Blob URL 的生命周期：

```javascript
class BlobURLManager {
    constructor() {
        this.urls = new Set();
    }

    create(blob) {
        const url = URL.createObjectURL(blob);
        this.urls.add(url);
        return url;
    }

    revoke(url) {
        if (this.urls.has(url)) {
            URL.revokeObjectURL(url);
            this.urls.delete(url);
        }
    }

    revokeAll() {
        this.urls.forEach(url => URL.revokeObjectURL(url));
        this.urls.clear();
    }

    // 页面卸载时自动清理
    cleanup() {
        window.addEventListener('beforeunload', () => {
            this.revokeAll();
        });
    }
}

// 使用示例
const blobManager = new BlobURLManager();
blobManager.cleanup();

// 创建 URL
const url = blobManager.create(blob);
img.src = url;

// 释放 URL
img.onload = () => {
    blobManager.revoke(url);
};
```

---

## 性能验证

周三下午四点，你开始验证修复效果。

你重新部署了修复后的代码到测试环境，模拟了周五下午的用户高峰场景：100 个并发用户，每人上传 5 张图片。

修复前的内存占用曲线：

```
时间 0s:  500MB
时间 30s: 1.2GB
时间 60s: 2.1GB
时间 90s: 3.5GB (接近服务器上限)
```

修复后的内存占用曲线：

```
时间 0s:  500MB
时间 30s: 650MB
时间 60s: 720MB
时间 90s: 680MB (稳定)
```

"完美！" 你兴奋地说，"内存占用稳定在了一个合理的范围内。"

你又测试了其他性能指标：

**响应时间**：
- 修复前：平均 2.3 秒 (因为内存压力导致 GC 频繁)
- 修复后：平均 0.8 秒 (稳定)

**用户体验**：
- 修复前：高峰期上传失败率 15%
- 修复后：上传失败率 <0.1%

**服务器成本**：
- 修复前：需要 8GB 内存服务器
- 修复后：4GB 内存服务器足够

"这次优化不仅解决了内存泄漏，还降低了 50% 的服务器成本，" 你总结。

---

## 周四复盘

周四上午九点，你召集了技术团队进行复盘会议。

你在白板上写下了这次性能优化的关键收获：

### Blob 与文件处理的核心原则

**原则 1: Blob 是不可变的**

Blob 对象一旦创建，内容就无法修改。任何"修改"操作实际上都会创建新的 Blob。

```javascript
const blob1 = new Blob(['Hello']);
const blob2 = new Blob([blob1, ' World']);  // 创建新 Blob，blob1 不变

console.log(blob1.size);  // 5 (未改变)
console.log(blob2.size);  // 11 (新对象)

// Blob 的属性也是只读的
blob1.size = 100;  // 无效
console.log(blob1.size);  // 仍然是 5
```

**原则 2: Blob URL 必须手动释放**

`URL.createObjectURL()` 创建的 URL 会持有 Blob 的强引用，导致 Blob 无法被垃圾回收。

```javascript
// ❌ 错误：URL 泄漏
const url = URL.createObjectURL(blob);
img.src = url;
// blob 无法被回收，因为 url 仍然引用它

// ✅ 正确：手动释放
const url = URL.createObjectURL(blob);
img.src = url;
img.onload = () => {
    URL.revokeObjectURL(url);  // 释放引用
};
```

**原则 3: File 继承自 Blob**

File 对象是 Blob 的子类，拥有额外的 `name` 和 `lastModified` 属性。

```javascript
const blob = new Blob(['content'], { type: 'text/plain' });
const file = new File([blob], 'example.txt', {
    type: 'text/plain',
    lastModified: Date.now()
});

console.log(file instanceof Blob);  // true
console.log(file instanceof File);  // true
console.log(file.name);  // 'example.txt'
console.log(file.size);  // 7 (继承自 Blob)
```

**原则 4: Blob 切片操作不复制数据**

`Blob.slice()` 创建的是原 Blob 的视图，而非复制数据。

```javascript
const blob = new Blob(['Hello World'], { type: 'text/plain' });
const slice = blob.slice(0, 5);  // 不复制数据，只是创建视图

console.log(slice.size);  // 5
console.log(blob.size);  // 11 (未改变)

// slice 和 blob 共享底层数据
// 只有在读取时才会实际复制
```

**原则 5: Blob 转换的最佳实践**

不同场景下，选择合适的 Blob 转换方式。

```javascript
// 场景 1: Blob → ArrayBuffer (完整读取)
async function blobToArrayBuffer(blob) {
    return await blob.arrayBuffer();
}

// 场景 2: Blob → Text (文本内容)
async function blobToText(blob) {
    return await blob.text();
}

// 场景 3: Blob → Data URL (base64，用于预览)
function blobToDataURL(blob) {
    return new Promise((resolve) => {
        const reader = new FileReader();
        reader.onload = (e) => resolve(e.target.result);
        reader.readAsDataURL(blob);
    });
}

// 场景 4: Blob → 流式读取 (大文件)
async function blobToStream(blob) {
    const stream = blob.stream();
    const reader = stream.getReader();

    while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        console.log('读取块:', value);
    }
}
```

**原则 6: 内存管理最佳实践**

```javascript
// ✅ 最佳实践 1: 及时释放 Blob URL
class ImageUploader {
    constructor() {
        this.currentURL = null;
    }

    setPreview(blob) {
        // 清理旧 URL
        if (this.currentURL) {
            URL.revokeObjectURL(this.currentURL);
        }

        // 创建新 URL
        this.currentURL = URL.createObjectURL(blob);
        document.querySelector('#preview').src = this.currentURL;
    }

    cleanup() {
        if (this.currentURL) {
            URL.revokeObjectURL(this.currentURL);
            this.currentURL = null;
        }
    }
}

// ✅ 最佳实践 2: 使用 Data URL 替代 Blob URL (小文件)
// Blob URL 需要手动释放，Data URL 会自动释放
async function setPreviewSmall(blob) {
    if (blob.size < 1024 * 1024) {  // 小于 1MB
        // 使用 Data URL
        const dataURL = await blob.text();
        img.src = dataURL;
    } else {
        // 使用 Blob URL (更高效)
        const url = URL.createObjectURL(blob);
        img.src = url;
        img.onload = () => URL.revokeObjectURL(url);
    }
}

// ✅ 最佳实践 3: 分块处理大文件
async function processLargeBlob(blob) {
    const chunkSize = 1024 * 1024;  // 1MB 每块
    let offset = 0;

    while (offset < blob.size) {
        const chunk = blob.slice(offset, offset + chunkSize);
        await processChunk(chunk);  // 处理单个块
        offset += chunkSize;
    }
}
```

---

## 性能优化总结

周四下午五点，你在 Wiki 上更新了文件上传优化的最佳实践文档。

**问题根因**：
- Blob URL 创建后未释放，导致 Blob 对象无法被垃圾回收
- 高并发场景下，内存占用呈线性增长，最终耗尽服务器内存

**优化效果**：
- 内存占用：从 3.5GB 降至 680MB (降低 81%)
- 响应时间：从 2.3 秒降至 0.8 秒 (提升 65%)
- 服务器成本：从 8GB 降至 4GB (节省 50%)
- 上传失败率：从 15% 降至 <0.1% (提升 99%)

**核心教训**：
- Blob 是不可变的，每次操作都会创建新对象
- Blob URL 必须手动释放，否则会导致内存泄漏
- 大文件处理应使用分块策略，避免内存峰值
- 性能监控是发现问题的第一步，定期检查内存和响应时间

你关上电脑，长舒一口气。这次性能优化从周一的监控告警到周四的完整修复，整个过程让你对 Blob 对象有了全新的理解。

"不可变性是优势，也是陷阱，" 你想，"关键在于理解它的内存管理机制。"

---

## 知识档案

**事故档案编号**: NETWORK-2024-1943
**影响范围**: Blob, File, URL.createObjectURL, 内存泄漏, 性能优化
**根本原因**: Blob URL 创建后未释放，持有 Blob 强引用导致内存泄漏
**学习成本**: 中 (需理解 Blob 不可变性和 URL 生命周期管理)

这是 JavaScript 世界第 143 次被记录的网络与数据事故。Blob 对象是浏览器中表示二进制数据的基本单位，具有不可变性——一旦创建，内容无法修改。任何"修改"操作都会创建新的 Blob 对象。File 对象继承自 Blob，添加了文件名和修改时间等元数据。Blob URL 通过 `URL.createObjectURL()` 创建，用于在浏览器中引用 Blob 数据，但会持有 Blob 的强引用，必须通过 `URL.revokeObjectURL()` 手动释放，否则会导致内存泄漏。在高并发场景下，未释放的 Blob URL 会导致内存占用线性增长，最终耗尽服务器资源。理解 Blob 的不可变性和正确管理 Blob URL 的生命周期是避免内存泄漏的关键。

---
