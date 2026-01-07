《第 45 次记录：递归与栈溢出事故 —— 函数的自我调用陷阱》

---

## 紧急事故

周四下午 3 点 47 分，生产环境监控突然全部变红。

你的手机震动了，Slack 频道炸开了锅。运维部门 @channel："文档管理系统崩溃，所有用户无法访问！" 客服部门："用户投诉电话打爆了！" 技术总监："谁负责这个模块？立刻排查！"

你的心跳瞬间加速。文档管理系统是你两周前重构的核心模块，上线后一直运行稳定。但现在，Sentry 错误追踪平台显示：过去 5 分钟内收到 1,247 个相同的错误报告。

你点开第一条错误堆栈：

```
Uncaught RangeError: Maximum call stack size exceeded
    at traverseDocumentTree (document-manager.js:156)
    at traverseDocumentTree (document-manager.js:163)
    at traverseDocumentTree (document-manager.js:163)
    at traverseDocumentTree (document-manager.js:163)
    ... (repeated 10,481 times)
```

栈溢出。这是最危险的错误类型之一——浏览器调用栈被耗尽，页面直接崩溃，没有任何恢复的机会。

你立刻打开 Chrome DevTools，访问生产环境的文档管理页面。页面加载到 60% 就卡住了，然后浏览器标签页突然变灰，显示："Aw, Snap! Something went wrong while displaying this webpage. Error code: OUT_OF_MEMORY"

"这不可能..." 你喃喃自语。你的代码经过了完整的测试，测试环境从未出现过栈溢出。

技术总监发来私信："还有多久能修复？客户在等。"

你快速切换到代码编辑器，找到出错的函数：

```javascript
function traverseDocumentTree(node) {
    console.log('Processing:', node.title)

    // 收集文档元数据
    if (node.type === 'document') {
        documentList.push({
            id: node.id,
            title: node.title,
            author: node.author
        })
    }

    // 递归遍历子节点
    node.children.forEach(child => {
        traverseDocumentTree(child)
    })
}
```

代码看起来很正常——标准的树遍历递归。你在测试环境用 50 个节点的文档树测试过，运行完美。但现在生产环境有 5,247 个文档节点...

等等。你突然意识到一个可怕的可能性：如果某个文档节点的 `children` 数组中包含了它的父节点，就会形成循环引用。递归会陷入无限循环，直到栈溢出。

你打开数据库查询工具，快速检查生产数据：

```sql
SELECT d1.id, d1.title, d2.id as child_id, d2.title as child_title
FROM documents d1
JOIN document_relations dr ON d1.id = dr.parent_id
JOIN documents d2 ON dr.child_id = d2.id
WHERE d2.id IN (
    SELECT parent_id FROM document_relations WHERE child_id = d1.id
)
```

查询结果让你倒吸一口凉气：有 3 个文档存在循环引用。上周有个实习生在测试批量导入功能时，错误地创建了父子关系的循环引用，而数据验证逻辑没有捕获到这个错误。

你看了看时钟：3 点 52 分。距离故障发生已经过去 5 分钟。每一秒钟，都有数百个用户在刷新页面，遇到崩溃。

"必须立刻修复。" 你打开编辑器，手指悬停在键盘上。但你知道，仅仅删除循环引用的数据还不够——你需要在代码层面彻底防止这类问题再次发生。

运维部门又发来消息："用户投诉还在增加，能否先回滚代码？"

"不行，" 你回复，"回滚也解决不了数据问题。我需要 10 分钟修复根本原因。"

你深吸一口气，开始排查递归函数的每一个细节。

---

## 追踪线索

你在本地创建了一个紧急测试文件，决心彻底搞清楚递归的边界条件和安全机制。

**第一步：复现栈溢出**

你首先需要确认浏览器的调用栈限制到底是多少。你写下测试代码：

```javascript
// 测试调用栈深度限制
function testStackDepth(depth = 0) {
    try {
        return testStackDepth(depth + 1)
    } catch (e) {
        console.log(`栈溢出深度: ${depth}`)
        console.log('错误信息:', e.message)
        return depth
    }
}

const maxDepth = testStackDepth()
```

Chrome 控制台输出：

```
栈溢出深度: 10481
错误信息: Maximum call stack size exceeded
```

"10,481 层..." 你记录下来。你又在 Firefox 和 Safari 中测试：

```
Firefox: 50,685 层
Safari: 41,753 层
```

不同浏览器的调用栈限制差异巨大。这意味着在 Chrome 中崩溃的代码，在 Firefox 中可能正常运行。

你意识到生产环境的文档树深度可能超过了 Chrome 的限制。你快速查询数据库：

```sql
WITH RECURSIVE tree_depth AS (
    SELECT id, title, 0 as depth
    FROM documents
    WHERE parent_id IS NULL

    UNION ALL

    SELECT d.id, d.title, td.depth + 1
    FROM documents d
    JOIN tree_depth td ON d.parent_id = td.id
    WHERE td.depth < 100
)
SELECT MAX(depth) as max_depth FROM tree_depth;
```

结果让你震惊：

```
max_depth: 83
```

正常的文档树深度是 83 层。虽然没有超过浏览器的 10,481 层限制，但如果存在循环引用，递归会在几秒钟内达到限制。

**第二步：分析递归的性能开销**

你创建了一个简单的性能对比测试：

```javascript
// 递归方式求和
function sumRecursive(n) {
    if (n <= 0) return 0
    return n + sumRecursive(n - 1)
}

// 循环方式求和
function sumLoop(n) {
    let sum = 0
    for (let i = 1; i <= n; i++) {
        sum += i
    }
    return sum
}

// 性能测试
console.time('递归求和 10,000')
const result1 = sumRecursive(10000)
console.timeEnd('递归求和 10,000')

console.time('循环求和 10,000')
const result2 = sumLoop(10000)
console.timeEnd('循环求和 10,000')
```

Chrome 控制台输出：

```
递归求和 10,000: 4.832ms
循环求和 10,000: 0.251ms
```

递归慢了将近 **19 倍**。你打开 Chrome DevTools 的 Performance 面板，录制了递归执行的性能剖析：

```
Function Call
├─ sumRecursive (n=10000) - 0.05ms
│  ├─ sumRecursive (n=9999) - 0.05ms
│  │  ├─ sumRecursive (n=9998) - 0.05ms
│  │  │  └─ ... (10,000 层调用)
│  │  └─ return 9998 + ... - 0.02ms
│  └─ return 9999 + ... - 0.02ms
└─ return 10000 + ... - 0.02ms

Total Time: 4.832ms
Stack Frames: 10,000
```

每次递归调用都需要：
1. 创建新的栈帧（存储局部变量、返回地址）
2. 执行函数调用开销（参数传递、上下文切换）
3. 等待子调用返回后再继续

循环则没有这些开销，直接在同一个栈帧中累加。

**第三步：测试斐波那契的性能灾难**

你想起了经典的递归陷阱——斐波那契数列：

```javascript
function fib(n) {
    if (n <= 2) return 1
    return fib(n - 1) + fib(n - 2)
}

console.time('fib(30)')
console.log('fib(30) =', fib(30))
console.timeEnd('fib(30)')

console.time('fib(35)')
console.log('fib(35) =', fib(35))
console.timeEnd('fib(35)')

console.time('fib(40)')
console.log('fib(40) =', fib(40))
console.timeEnd('fib(40)')
```

输出让你震惊：

```
fib(30) = 832040
fib(30): 87.234ms

fib(35) = 9227465
fib(35): 982.145ms

fib(40) = 102334155
fib(40): 11247.628ms  // 11.2 秒！
```

每增加 5，执行时间增长约 **10 倍**。这是指数级增长的典型表现。

你在 Chrome DevTools 的 Call Tree 视图中查看：

```
fib(40)
├─ fib(39) - 调用 1 次
│  ├─ fib(38) - 调用 1 次
│  │  ├─ fib(37) - 调用 1 次
│  │  └─ fib(36) - 调用 1 次
│  └─ fib(37) - 调用 1 次（重复计算！）
│     ├─ fib(36) - 调用 1 次（重复计算！）
│     └─ fib(35) - 调用 1 次（重复计算！）
└─ fib(38) - 调用 1 次（重复计算！）
   └─ ... (大量重复计算)
```

`fib(38)` 被计算了 **2 次**，`fib(37)` 被计算了 **3 次**，`fib(36)` 被计算了 **5 次**...这是灾难性的重复计算。

你快速计算了一下：`fib(40)` 的总调用次数接近 **2^40 = 1,099,511,627,776 次**（万亿级）。虽然实际调用次数没有这么多（因为到达 `n <= 2` 就终止了），但仍然是天文数字。

**第四步：记忆化优化实验**

你决定尝试用缓存来避免重复计算：

```javascript
function createFibMemo() {
    const cache = {}

    function fib(n) {
        if (n in cache) {
            return cache[n]
        }

        if (n <= 2) {
            cache[n] = 1
            return 1
        }

        const result = fib(n - 1) + fib(n - 2)
        cache[n] = result
        return result
    }

    return fib
}

const fibMemo = createFibMemo()

console.time('fibMemo(40)')
console.log('fibMemo(40) =', fibMemo(40))
console.timeEnd('fibMemo(40)')

console.time('fibMemo(100)')
console.log('fibMemo(100) =', fibMemo(100))
console.timeEnd('fibMemo(100)')
```

输出让你兴奋：

```
fibMemo(40) = 102334155
fibMemo(40): 1.028ms  // 从 11,247ms 降到 1ms！

fibMemo(100) = 354224848179262000000
fibMemo(100): 0.156ms  // 更大的数反而更快！
```

性能提升了 **10,946 倍**！Cache 命中率接近 100%，每个 `fib(n)` 只计算一次。

你在 Memory 面板中查看缓存对象：

```javascript
// 在控制台输入
fibMemo.toString()  // 无法直接访问 cache

// 需要修改代码暴露 cache
function createFibMemo() {
    const cache = {}

    function fib(n) {
        if (n in cache) return cache[n]
        if (n <= 2) return cache[n] = 1
        return cache[n] = fib(n - 1) + fib(n - 2)
    }

    fib.cache = cache  // 暴露缓存
    return fib
}

const fibMemo = createFibMemo()
fibMemo(40)
console.log('缓存大小:', Object.keys(fibMemo.cache).length)  // 40
console.log('缓存内容:', fibMemo.cache)
```

输出：

```javascript
缓存大小: 40
缓存内容: {
  '1': 1,
  '2': 1,
  '3': 2,
  '4': 3,
  '5': 5,
  ...
  '40': 102334155
}
```

缓存只存储了 40 个值，但避免了数十亿次重复计算。

**第五步：发现循环引用的致命威胁**

你回到生产问题的核心——循环引用。你创建了一个模拟场景：

```javascript
const node1 = { id: 1, title: 'Document 1', children: [] }
const node2 = { id: 2, title: 'Document 2', children: [] }
const node3 = { id: 3, title: 'Document 3', children: [] }

// 创建循环引用
node1.children.push(node2)
node2.children.push(node3)
node3.children.push(node1)  // 循环！

// 危险的递归
function traverse(node) {
    console.log(node.title)
    node.children.forEach(child => traverse(child))
}

// traverse(node1)  // 不要运行！会栈溢出
```

你需要一个安全的检测机制。你尝试用 `Set` 记录已访问的节点：

```javascript
function traverseSafe(node, visited = new Set()) {
    if (visited.has(node.id)) {
        console.warn('检测到循环引用:', node.id)
        return
    }

    visited.add(node.id)
    console.log(node.title)

    node.children.forEach(child => {
        traverseSafe(child, visited)
    })
}

traverseSafe(node1)
```

输出：

```
Document 1
Document 2
Document 3
检测到循环引用: 1
```

完美！循环引用被检测并阻止了。

但你突然意识到一个问题：如果节点对象本身（而非 `id`）形成循环呢？

```javascript
const objNode1 = { title: 'A', children: [] }
const objNode2 = { title: 'B', children: [] }

objNode1.children.push(objNode2)
objNode2.children.push(objNode1)  // 对象循环引用

function traverseObject(node, visited = new Set()) {
    if (visited.has(node)) {
        console.warn('检测到对象循环引用:', node.title)
        return
    }

    visited.add(node)
    console.log(node.title)

    node.children.forEach(child => {
        traverseObject(child, visited)
    })
}

traverseObject(objNode1)
```

输出：

```
A
B
检测到对象循环引用: A
```

`Set` 可以存储对象引用，直接检测对象级别的循环。

你看了看时钟：4 点 02 分。你已经找到了问题的根源和解决方案。现在需要编写生产级的修复代码。

---

## 定位根因

你整理了调查结果，准备编写一个完整的、生产级的递归遍历工具类。

**问题代码：缺少安全机制**

```javascript
// ❌ 危险：没有任何保护
function traverseDocumentTree(node) {
    console.log('Processing:', node.title)

    if (node.type === 'document') {
        documentList.push({
            id: node.id,
            title: node.title
        })
    }

    // 致命缺陷：
    // 1. 没有检查 node 是否为 null/undefined
    // 2. 没有检查 children 是否存在
    // 3. 没有检测循环引用
    // 4. 没有限制递归深度
    // 5. 没有错误处理
    node.children.forEach(child => {
        traverseDocumentTree(child)
    })
}
```

**修复方案 1：添加基本安全检查**

```javascript
// ✅ 基本安全版本
function traverseDocumentTreeBasic(node) {
    // 终止条件 1：节点为空
    if (!node) {
        console.warn('遇到空节点')
        return
    }

    console.log('Processing:', node.title)

    if (node.type === 'document') {
        documentList.push({
            id: node.id,
            title: node.title
        })
    }

    // 终止条件 2：没有子节点
    if (!node.children || node.children.length === 0) {
        return
    }

    // 终止条件 3：children 不是数组
    if (!Array.isArray(node.children)) {
        console.warn('children 不是数组:', typeof node.children)
        return
    }

    node.children.forEach(child => {
        traverseDocumentTreeBasic(child)
    })
}
```

**修复方案 2：添加循环引用检测**

```javascript
// ✅ 带循环检测的版本
function traverseWithCycleDetection(node, visited = new Set()) {
    if (!node) return

    // 循环引用检测
    if (visited.has(node.id)) {
        console.error(`检测到循环引用: ${node.id} - ${node.title}`)
        return
    }

    visited.add(node.id)

    console.log('Processing:', node.title)

    if (node.type === 'document') {
        documentList.push({
            id: node.id,
            title: node.title
        })
    }

    if (!node.children || !Array.isArray(node.children)) return

    node.children.forEach(child => {
        traverseWithCycleDetection(child, visited)
    })
}
```

**修复方案 3：添加深度限制**

```javascript
// ✅ 带深度限制的版本
function traverseWithDepthLimit(node, options = {}) {
    const {
        maxDepth = 100,
        currentDepth = 0,
        visited = new Set()
    } = options

    if (!node) return

    // 深度检查
    if (currentDepth > maxDepth) {
        console.error(`递归深度超过限制 ${maxDepth}，当前深度 ${currentDepth}`)
        throw new Error(`MAX_RECURSION_DEPTH_EXCEEDED: ${currentDepth}`)
    }

    // 循环检测
    if (visited.has(node.id)) {
        console.warn(`循环引用: ${node.id} 在深度 ${currentDepth}`)
        return
    }

    visited.add(node.id)

    console.log('  '.repeat(currentDepth) + node.title)

    if (node.type === 'document') {
        documentList.push({
            id: node.id,
            title: node.title,
            depth: currentDepth
        })
    }

    if (!node.children || !Array.isArray(node.children)) return

    node.children.forEach(child => {
        traverseWithDepthLimit(child, {
            maxDepth,
            currentDepth: currentDepth + 1,
            visited
        })
    })
}
```

**完整的生产级解决方案**

```javascript
class RecursionTraverser {
    constructor(options = {}) {
        this.maxDepth = options.maxDepth || 100
        this.onNode = options.onNode || ((node) => console.log(node.title))
        this.onCycle = options.onCycle || ((node) => console.warn('Cycle:', node.id))
        this.onDepthExceeded = options.onDepthExceeded || ((node, depth) => {
            throw new Error(`Max depth ${depth} exceeded at node ${node.id}`)
        })

        this.visited = new Set()
        this.stats = {
            nodesProcessed: 0,
            cyclesDetected: 0,
            maxDepthReached: 0,
            errors: []
        }
    }

    traverse(node, currentDepth = 0) {
        // 空节点检查
        if (!node) {
            this.stats.errors.push('Encountered null node')
            return
        }

        // 深度检查
        if (currentDepth > this.maxDepth) {
            this.stats.errors.push(`Depth exceeded at ${node.id}`)
            this.onDepthExceeded(node, currentDepth)
            return
        }

        // 循环检测
        if (this.visited.has(node.id)) {
            this.stats.cyclesDetected++
            this.onCycle(node)
            return
        }

        // 记录访问
        this.visited.add(node.id)
        this.stats.nodesProcessed++
        this.stats.maxDepthReached = Math.max(
            this.stats.maxDepthReached,
            currentDepth
        )

        // 处理当前节点
        try {
            this.onNode(node, currentDepth)
        } catch (error) {
            this.stats.errors.push(`Error processing ${node.id}: ${error.message}`)
            return
        }

        // 遍历子节点
        if (!node.children || !Array.isArray(node.children)) {
            return
        }

        for (const child of node.children) {
            this.traverse(child, currentDepth + 1)
        }
    }

    reset() {
        this.visited.clear()
        this.stats = {
            nodesProcessed: 0,
            cyclesDetected: 0,
            maxDepthReached: 0,
            errors: []
        }
    }

    getStats() {
        return { ...this.stats }
    }
}

// 使用示例
const traverser = new RecursionTraverser({
    maxDepth: 100,
    onNode: (node, depth) => {
        console.log('  '.repeat(depth) + `[${depth}] ${node.title}`)

        if (node.type === 'document') {
            documentList.push({
                id: node.id,
                title: node.title,
                depth: depth
            })
        }
    },
    onCycle: (node) => {
        console.error(`❌ 循环引用: ${node.id} - ${node.title}`)
    },
    onDepthExceeded: (node, depth) => {
        console.error(`❌ 深度超限: ${node.id} at depth ${depth}`)
    }
})

// 遍历文档树
traverser.traverse(rootNode)

// 查看统计
console.log('遍历统计:', traverser.getStats())
// {
//   nodesProcessed: 5247,
//   cyclesDetected: 3,
//   maxDepthReached: 83,
//   errors: []
// }
```

**Chrome DevTools 调试技巧**

你打开 Chrome DevTools 的 Sources 面板，在 `traverse` 方法的第一行设置条件断点：

```javascript
// 条件断点：只在深度 > 80 时暂停
currentDepth > 80
```

然后点击 Continue，调试器在深度 81 时暂停。你在 Call Stack 面板中看到：

```
traverse (currentDepth: 81)
  traverse (currentDepth: 80)
    traverse (currentDepth: 79)
      ...
        traverse (currentDepth: 1)
          traverse (currentDepth: 0)
```

完整的 81 层调用栈。你可以点击任意一层查看当时的 `node` 对象和 `visited` Set 的状态。

**性能优化：尾递归改迭代**

你意识到对于深层文档树，递归可能仍然不够高效。你将递归改写为迭代：

```javascript
function traverseIterative(rootNode) {
    const stack = [{ node: rootNode, depth: 0 }]
    const visited = new Set()

    while (stack.length > 0) {
        const { node, depth } = stack.pop()

        // 所有检查逻辑与递归版本相同
        if (!node) continue
        if (depth > 100) {
            console.error('深度超限')
            continue
        }
        if (visited.has(node.id)) {
            console.warn('循环引用:', node.id)
            continue
        }

        visited.add(node.id)
        console.log('  '.repeat(depth) + node.title)

        // 将子节点压入栈（注意顺序）
        if (node.children && Array.isArray(node.children)) {
            // 倒序压栈，保证按正确顺序弹出
            for (let i = node.children.length - 1; i >= 0; i--) {
                stack.push({
                    node: node.children[i],
                    depth: depth + 1
                })
            }
        }
    }
}
```

性能测试：

```javascript
const largeTree = createTree(5000, 10)  // 5000 个节点，平均深度 10

console.time('递归遍历')
traverseRecursive(largeTree)
console.timeEnd('递归遍历')
// 递归遍历: 42.156ms

console.time('迭代遍历')
traverseIterative(largeTree)
console.timeEnd('迭代遍历')
// 迭代遍历: 28.734ms
```

迭代版本快了 **31%**，且没有栈溢出风险。

你将修复后的代码推送到测试环境，运行了完整的测试套件：

```javascript
// 测试用例 1：正常树
const normalTree = {
    id: 1, title: 'Root',
    children: [
        { id: 2, title: 'Child 1', children: [] },
        { id: 3, title: 'Child 2', children: [] }
    ]
}
traverser.traverse(normalTree)
// ✅ 通过

// 测试用例 2：循环引用
const node1 = { id: 1, title: 'A', children: [] }
const node2 = { id: 2, title: 'B', children: [] }
node1.children.push(node2)
node2.children.push(node1)
traverser.traverse(node1)
// ✅ 检测到循环，不崩溃

// 测试用例 3：深层嵌套
const deepTree = createDeepTree(200)
traverser.traverse(deepTree)
// ✅ 深度限制生效，不栈溢出

// 测试用例 4：空节点
traverser.traverse(null)
// ✅ 安全返回

// 测试用例 5：错误的 children
const badNode = { id: 1, title: 'Bad', children: 'not-array' }
traverser.traverse(badNode)
// ✅ 类型检查通过
```

所有测试通过。你看了看时钟：4 点 11 分。从故障发生到修复完成，用了 24 分钟。

你将代码部署到生产环境，监控显示错误率从 100% 降到 0。用户可以正常访问文档管理系统了。

技术总监发来消息："修复了？干得漂亮。明天写个事故报告，分析一下根本原因。"

---

## 递归机制详解

你在事故报告中详细记录了递归的核心原理和最佳实践。

**核心原理 1：递归的三要素**

```javascript
function recursion(n) {
    // 1. 终止条件（Base Case）
    // 必须存在，否则无限递归导致栈溢出
    if (n <= 0) {
        return 0
    }

    // 2. 递归调用（Recursive Call）
    // 函数调用自身
    const result = recursion(n - 1)

    // 3. 问题规模缩小（Problem Reduction）
    // 每次递归必须让问题更小，确保最终达到终止条件
    // n -> n-1 -> n-2 -> ... -> 0
    return n + result
}
```

**核心原理 2：调用栈机制**

```javascript
function factorial(n) {
    console.log(`调用 factorial(${n})`)

    if (n <= 1) {
        console.log(`返回 1 (终止条件)`)
        return 1
    }

    const result = n * factorial(n - 1)
    console.log(`factorial(${n}) 返回 ${result}`)
    return result
}

factorial(4)
```

输出展示了调用栈的构建和展开过程：

```
调用 factorial(4)
调用 factorial(3)
调用 factorial(2)
调用 factorial(1)
返回 1 (终止条件)
factorial(2) 返回 2
factorial(3) 返回 6
factorial(4) 返回 24
```

在 Chrome DevTools 中，你可以看到调用栈的实时状态：

```
Call Stack:
  factorial (n=1)    <- 最内层调用
    factorial (n=2)
      factorial (n=3)
        factorial (n=4)  <- 最外层调用
```

每一层调用都会占用栈空间，存储：
- 局部变量（`n`、`result`）
- 返回地址（函数返回后继续执行的位置）
- 调用上下文（`this` 值、作用域链）

**核心原理 3：经典递归模式**

**模式 1：线性递归（Linear Recursion）**

```javascript
// 阶乘：n! = n × (n-1)!
function factorial(n) {
    if (n <= 1) return 1
    return n * factorial(n - 1)
}

// 数组求和
function sumArray(arr, index = 0) {
    if (index >= arr.length) return 0
    return arr[index] + sumArray(arr, index + 1)
}
```

**模式 2：二叉递归（Binary Recursion）**

```javascript
// 斐波那契：f(n) = f(n-1) + f(n-2)
function fib(n) {
    if (n <= 2) return 1
    return fib(n - 1) + fib(n - 2)  // 两次递归调用
}

// 计算组合数 C(n, k) = C(n-1, k-1) + C(n-1, k)
function combination(n, k) {
    if (k === 0 || k === n) return 1
    return combination(n - 1, k - 1) + combination(n - 1, k)
}
```

**模式 3：多路递归（Multi-way Recursion）**

```javascript
// 树遍历
function traverseTree(node) {
    if (!node) return

    console.log(node.value)

    // 每个子节点都递归
    node.children.forEach(child => {
        traverseTree(child)
    })
}
```

**核心原理 4：尾递归优化（TCO）**

```javascript
// ❌ 非尾递归：递归调用后还有操作
function factorial(n) {
    if (n <= 1) return 1
    return n * factorial(n - 1)  // 返回后还要乘以 n
}

// ✅ 尾递归：递归调用是最后一个操作
function factorialTail(n, acc = 1) {
    if (n <= 1) return acc
    return factorialTail(n - 1, n * acc)  // 直接返回递归结果
}
```

尾递归的优势：编译器可以将其优化为循环，不增加调用栈。但注意：**JavaScript 引擎对尾递归优化的支持有限**。

Chrome 和 Firefox 默认不支持 TCO。只有 Safari 在严格模式下支持。

**尾递归的替代方案：Trampoline 模式**

```javascript
function trampoline(fn) {
    return function(...args) {
        let result = fn(...args)

        while (typeof result === 'function') {
            result = result()
        }

        return result
    }
}

function factorialTrampoline(n, acc = 1) {
    if (n <= 1) return acc
    return () => factorialTrampoline(n - 1, n * acc)
}

const factorial = trampoline(factorialTrampoline)
console.log(factorial(10000))  // 不会栈溢出！
```

**核心原理 5：递归转迭代的通用模式**

任何递归都可以用显式栈转换为迭代：

```javascript
// 递归版本
function sumRecursive(n) {
    if (n <= 0) return 0
    return n + sumRecursive(n - 1)
}

// 迭代版本（模拟调用栈）
function sumIterative(n) {
    const stack = []
    let result = 0

    // 模拟递归的"下降"阶段
    while (n > 0) {
        stack.push(n)
        n--
    }

    // 模拟递归的"上升"阶段
    while (stack.length > 0) {
        result += stack.pop()
    }

    return result
}
```

**核心原理 6：循环引用检测的两种方式**

**方式 1：ID 检测（适用于有唯一标识的节点）**

```javascript
function traverse(node, visited = new Set()) {
    if (visited.has(node.id)) {
        console.warn('循环引用:', node.id)
        return
    }

    visited.add(node.id)
    console.log(node.title)

    if (node.children) {
        node.children.forEach(child => traverse(child, visited))
    }
}
```

**方式 2：对象引用检测（适用于任意对象）**

```javascript
function traverse(node, visited = new WeakSet()) {
    if (visited.has(node)) {
        console.warn('循环引用:', node)
        return
    }

    visited.add(node)
    console.log(node.title)

    if (node.children) {
        node.children.forEach(child => traverse(child, visited))
    }
}
```

使用 `WeakSet` 的优势：不会阻止垃圾回收。当节点对象不再被其他地方引用时，`WeakSet` 中的引用会自动清除。

**核心原理 7：深度限制的实现**

```javascript
function traverseWithLimit(node, maxDepth = 100, currentDepth = 0) {
    if (currentDepth > maxDepth) {
        throw new Error(`递归深度超过 ${maxDepth}`)
    }

    console.log('  '.repeat(currentDepth) + node.title)

    if (node.children) {
        node.children.forEach(child => {
            traverseWithLimit(child, maxDepth, currentDepth + 1)
        })
    }
}
```

推荐的深度限制值：
- **简单递归**（如阶乘）：1000-5000
- **树遍历**：100-500（取决于预期树深度）
- **图遍历**：50-200（图可能有复杂路径）

**核心原理 8：记忆化（Memoization）的通用实现**

```javascript
function memoize(fn) {
    const cache = new Map()

    return function(...args) {
        const key = JSON.stringify(args)

        if (cache.has(key)) {
            return cache.get(key)
        }

        const result = fn(...args)
        cache.set(key, result)
        return result
    }
}

// 使用记忆化
const fib = memoize(function(n) {
    if (n <= 2) return 1
    return fib(n - 1) + fib(n - 2)
})

console.time('fib(40)')
console.log(fib(40))  // 第一次调用
console.timeEnd('fib(40)')  // ~1ms

console.time('fib(40) again')
console.log(fib(40))  // 第二次调用
console.timeEnd('fib(40) again')  // ~0.01ms（从缓存读取）
```

注意：`JSON.stringify(args)` 对于复杂对象可能性能较差。对于对象参数，可以使用 `WeakMap`：

```javascript
function memoizeObject(fn) {
    const cache = new WeakMap()

    return function(obj) {
        if (cache.has(obj)) {
            return cache.get(obj)
        }

        const result = fn(obj)
        cache.set(obj, result)
        return result
    }
}
```

**核心原理 9：递归的性能分析**

用 Chrome DevTools 的 Performance 面板分析递归性能：

1. 打开 Performance 面板
2. 点击 Record
3. 执行递归函数
4. 停止录制

在 Bottom-Up 视图中，你会看到：

```
Self Time | Total Time | Function
----------|------------|----------
2.1ms     | 45.7ms     | fib
0.8ms     | 12.3ms     | factorial
```

- **Self Time**：函数自身执行时间（不包括子调用）
- **Total Time**：函数总时间（包括所有子调用）

如果 Total Time 远大于 Self Time，说明大部分时间花在递归调用上。

**核心原理 10：递归的适用场景**

**适合递归的场景：**

1. **树形结构遍历**
   ```javascript
   function countNodes(tree) {
       if (!tree) return 0
       return 1 + tree.children.reduce((sum, child) =>
           sum + countNodes(child), 0
       )
   }
   ```

2. **分治算法**
   ```javascript
   function quickSort(arr) {
       if (arr.length <= 1) return arr

       const pivot = arr[0]
       const left = arr.slice(1).filter(x => x < pivot)
       const right = arr.slice(1).filter(x => x >= pivot)

       return [...quickSort(left), pivot, ...quickSort(right)]
   }
   ```

3. **回溯算法**
   ```javascript
   function permute(arr) {
       if (arr.length === 0) return [[]]

       const result = []
       for (let i = 0; i < arr.length; i++) {
           const rest = [...arr.slice(0, i), ...arr.slice(i + 1)]
           const perms = permute(rest)
           perms.forEach(p => result.push([arr[i], ...p]))
       }
       return result
   }
   ```

**不适合递归的场景：**

1. **简单循环累加**
   ```javascript
   // ❌ 递归：慢且可能栈溢出
   function sum(n) {
       if (n <= 0) return 0
       return n + sum(n - 1)
   }

   // ✅ 循环：快速高效
   function sum(n) {
       let result = 0
       for (let i = 1; i <= n; i++) {
           result += i
       }
       return result
   }
   ```

2. **大规模数据处理**
   ```javascript
   // ❌ 递归：处理 10 万条数据会栈溢出
   function processArray(arr, index = 0) {
       if (index >= arr.length) return
       process(arr[index])
       processArray(arr, index + 1)
   }

   // ✅ 循环：没有调用栈限制
   function processArray(arr) {
       for (const item of arr) {
           process(item)
       }
   }
   ```

---

## 知识档案：递归机制的十大法则

**规则 1：递归的三要素缺一不可**

终止条件（Base Case）、递归调用（Recursive Call）、问题规模缩小（Problem Reduction）。缺少终止条件会无限递归导致栈溢出。缺少规模缩小会让递归永远无法达到终止条件。

```javascript
function countdown(n) {
    if (n <= 0) return '发射!'  // 终止条件
    console.log(n)
    return countdown(n - 1)  // 规模缩小：n -> n-1
}
```

**规则 2：调用栈是有限资源**

不同浏览器的调用栈限制：Chrome ~10,481 层，Firefox ~50,685 层，Safari ~41,753 层。超过限制会抛出 `RangeError: Maximum call stack size exceeded`。

```javascript
function testLimit() {
    let depth = 0
    try {
        (function recurse() {
            depth++
            recurse()
        })()
    } catch (e) {
        console.log('栈溢出深度:', depth)
    }
}
```

**规则 3：每次递归都有函数调用开销**

递归需要创建栈帧（存储局部变量、返回地址、调用上下文），导致性能开销。简单递归比循环慢 10-20 倍。

```javascript
// 性能对比
console.time('递归')
sumRecursive(10000)  // ~5ms
console.timeEnd('递归')

console.time('循环')
sumLoop(10000)  // ~0.5ms
console.timeEnd('循环')
```

**规则 4：重复计算是递归性能杀手**

斐波那契的朴素递归有指数级时间复杂度 O(2^n)，因为大量重复计算。`fib(40)` 需要 11 秒，`fib(50)` 需要数小时。

```javascript
function fib(n) {
    if (n <= 2) return 1
    return fib(n - 1) + fib(n - 2)
    // fib(5) 会计算 fib(3) 两次，fib(2) 三次
}
```

**规则 5：记忆化可以消除重复计算**

用缓存存储已计算的结果，将时间复杂度从 O(2^n) 降到 O(n)。斐波那契的记忆化版本比朴素版本快 **10,000+ 倍**。

```javascript
function fibMemo() {
    const cache = {}
    return function fib(n) {
        if (n in cache) return cache[n]
        if (n <= 2) return 1
        return cache[n] = fib(n - 1) + fib(n - 2)
    }
}
```

**规则 6：循环引用会导致无限递归**

树或图结构中，如果存在 A → B → A 的循环路径，递归会陷入死循环直到栈溢出。必须用 `Set` 或 `WeakSet` 记录已访问节点。

```javascript
function traverse(node, visited = new Set()) {
    if (visited.has(node.id)) return  // 检测循环
    visited.add(node.id)
    node.children?.forEach(child => traverse(child, visited))
}
```

**规则 7：深度限制是必要的安全机制**

即使没有循环引用，过深的递归（如 1000+ 层）也可能栈溢出。推荐在递归函数中添加深度计数器，超过阈值时抛出错误。

```javascript
function traverse(node, maxDepth = 100, depth = 0) {
    if (depth > maxDepth) {
        throw new Error(`递归深度超过 ${maxDepth}`)
    }
    // 处理逻辑
    node.children?.forEach(child => traverse(child, maxDepth, depth + 1))
}
```

**规则 8：尾递归优化在 JavaScript 中支持有限**

尾递归（递归调用是函数最后一个操作）理论上可以优化为循环，不增加调用栈。但 Chrome 和 Firefox 不支持 TCO，只有 Safari 在严格模式下支持。

```javascript
// 尾递归
function factorialTail(n, acc = 1) {
    if (n <= 1) return acc
    return factorialTail(n - 1, n * acc)  // 最后一个操作
}

// 但在 Chrome 中仍会栈溢出
factorialTail(100000)  // RangeError
```

**规则 9：任何递归都可以转换为迭代**

用显式栈模拟调用栈，可以将递归改写为迭代。迭代版本性能更好，且没有栈溢出风险。

```javascript
// 递归
function traverse(node) {
    console.log(node.value)
    node.children?.forEach(traverse)
}

// 迭代
function traverseIterative(root) {
    const stack = [root]
    while (stack.length) {
        const node = stack.pop()
        console.log(node.value)
        stack.push(...(node.children || []).reverse())
    }
}
```

**规则 10：递归适合声明式思维，循环适合命令式思维**

递归更符合问题的数学定义（如阶乘 n! = n × (n-1)!），代码简洁优雅。循环需要手动管理状态，但性能更好。根据场景选择：小规模、树形结构用递归；大规模、简单累加用循环。

```javascript
// 递归：声明式，简洁
function factorial(n) {
    return n <= 1 ? 1 : n * factorial(n - 1)
}

// 循环：命令式，高效
function factorial(n) {
    let result = 1
    for (let i = 2; i <= n; i++) {
        result *= i
    }
    return result
}
```

---

**事故档案编号**：JS-2024-1645
**影响范围**：调用栈、系统稳定性、性能、用户体验
**根本原因**：缺少终止条件、循环引用检测、深度限制、性能优化
**修复成本**：中等（添加安全机制，重构递归逻辑）
**预防措施**：递归函数必须包含终止条件、循环检测、深度限制；大规模数据考虑迭代；重复计算场景使用记忆化

这是 JavaScript 世界第 45 次被记录的递归事故。递归是函数自我调用的编程技术，需要三要素：终止条件（防止无限递归）、递归调用（函数调用自身）、问题规模缩小（确保最终达到终止条件）。调用栈是有限资源，浏览器限制在 10,000-50,000 层。循环引用和缺少深度限制会导致栈溢出崩溃。重复计算让性能呈指数下降，记忆化可以消除重复计算，性能提升数千倍。尾递归优化在 JavaScript 中支持有限。任何递归都可以转换为迭代，迭代更高效但代码复杂。递归适合树遍历、分治算法、回溯算法等声明式场景。理解递归，就理解了 JavaScript 如何通过函数的自我引用优雅地解决复杂问题，以及如何在性能和可读性之间做出权衡。
