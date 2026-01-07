《第 158 次记录: 周日上午的重构计划 —— IndexedDB 深度优化实战》

---

## 个人项目的瓶颈

周日上午 9 点半, 你坐在家里的书桌前, 打开了三天前开始的个人项目。

窗外阳光正好, 咖啡的香气在房间里弥漫。这是你最喜欢的编程时光——没有工作压力, 没有 deadline, 可以完全沉浸在技术探索中。

你正在开发一个离线笔记应用, 上周已经实现了基本功能: 创建、编辑、删除笔记。你用 IndexedDB 存储数据, 一开始感觉很不错——数据持久化、容量无限、API 也不难用。

但昨晚测试时, 你发现了一个性能问题。

当笔记数量超过 500 条时, 搜索功能变得很慢。你在搜索框输入关键词, 页面会卡顿 2-3 秒才显示结果。打开 Performance 面板, 你看到 `getAllNotes()` 函数占用了大量时间。

你看着代码, 皱起眉头:

```javascript
// 当前的搜索实现
async function searchNotes(keyword) {
    const db = await openDB();
    const transaction = db.transaction(['notes'], 'readonly');
    const objectStore = transaction.objectStore('notes');

    // ❌ 问题: 获取所有笔记, 然后在 JavaScript 中过滤
    const allNotes = await objectStore.getAll();

    return allNotes.filter(note =>
        note.title.includes(keyword) ||
        note.content.includes(keyword)
    );
}
```

"每次搜索都要读取 500 条笔记..." 你喃喃自语, "难怪这么慢。"

你想起上周在文档里看到过 IndexedDB 支持索引和游标, 但当时没深入研究。"也许是时候好好学习一下 IndexedDB 的高级特性了。"

你倒了一杯咖啡, 打开 MDN 文档, 开始系统地研究 IndexedDB。

---

## 索引系统的发现

你从索引开始研究。

文档说, IndexedDB 的索引类似于数据库的索引, 可以加速查询。你之前创建数据库时, 只设置了主键 `id`, 没有创建任何索引。

"如果给 `title` 和 `content` 加上索引, 搜索会不会快很多?" 你想。

你修改了数据库初始化代码:

```javascript
// 创建带索引的数据库
function openDB() {
    return new Promise((resolve, reject) => {
        const request = indexedDB.open('NotesDB', 2);  // 版本升级到 2

        request.onupgradeneeded = (event) => {
            const db = event.target.result;

            // 如果 notes 对象仓库已存在, 先删除
            if (db.objectStoreNames.contains('notes')) {
                db.deleteObjectStore('notes');
            }

            // 重新创建对象仓库
            const objectStore = db.createObjectStore('notes', {
                keyPath: 'id',
                autoIncrement: true
            });

            // ✅ 创建索引
            objectStore.createIndex('title', 'title', { unique: false });
            objectStore.createIndex('content', 'content', { unique: false });
            objectStore.createIndex('createdAt', 'createdAt', { unique: false });
            objectStore.createIndex('tags', 'tags', {
                unique: false,
                multiEntry: true  // 数组索引
            });

            console.log('数据库升级完成, 索引已创建');
        };

        request.onsuccess = (event) => {
            resolve(event.target.result);
        };

        request.onerror = (event) => {
            reject(event.target.error);
        };
    });
}
```

你注意到 `tags` 索引有个特殊的选项: `multiEntry: true`。

"这是什么意思?" 你查阅文档, 发现这是为数组字段设计的。如果一个笔记有 `tags: ['JavaScript', 'IndexedDB']`, 启用 `multiEntry` 后, 会为每个标签值创建一个索引条目。

"这样就能按标签快速查询了!" 你兴奋地说。

你刷新页面, 数据库自动升级, 索引创建完成。现在你想测试索引的效果。

---

## 游标遍历的优化

你开始重写搜索函数, 使用索引和游标。

首先, 你尝试通过 `title` 索引搜索:

```javascript
// 使用索引搜索 (方法 1: IDBKeyRange)
async function searchNotesByTitle(keyword) {
    const db = await openDB();
    const transaction = db.transaction(['notes'], 'readonly');
    const objectStore = transaction.objectStore('notes');
    const index = objectStore.index('title');

    // ✅ 使用 IDBKeyRange 进行范围查询
    const range = IDBKeyRange.bound(
        keyword,
        keyword + '\uffff',  // Unicode 最大字符
        false,
        false
    );

    const request = index.getAll(range);

    return new Promise((resolve, reject) => {
        request.onsuccess = () => {
            resolve(request.result);
        };

        request.onerror = () => {
            reject(request.error);
        };
    });
}
```

你测试了一下, 搜索 "JavaScript" 相关的笔记, 结果立即返回!

"太快了!" 你看着 Performance 面板, 搜索时间从 2-3 秒降到了 50ms。

但你很快发现一个问题: 这个方法只能搜索标题以关键词**开头**的笔记。如果关键词在标题中间, 就搜不到。

"需要更灵活的搜索..." 你想。

你决定使用游标 (Cursor) 来遍历索引, 自己实现模糊搜索:

```javascript
// 使用游标进行模糊搜索
async function searchNotesWithCursor(keyword) {
    const db = await openDB();
    const transaction = db.transaction(['notes'], 'readonly');
    const objectStore = transaction.objectStore('notes');
    const index = objectStore.index('title');

    const results = [];

    return new Promise((resolve, reject) => {
        // ✅ 打开游标
        const request = index.openCursor();

        request.onsuccess = (event) => {
            const cursor = event.target.result;

            if (cursor) {
                // 检查标题是否包含关键词
                if (cursor.value.title.includes(keyword)) {
                    results.push(cursor.value);
                }

                // 移动到下一个记录
                cursor.continue();
            } else {
                // 遍历完成
                resolve(results);
            }
        };

        request.onerror = () => {
            reject(request.error);
        };
    });
}
```

你测试后发现, 游标遍历比 `getAll()` 快很多, 但仍然比 `IDBKeyRange` 慢。

"看来需要权衡, " 你在笔记中写道, "如果需要精确匹配或前缀匹配, 用 `IDBKeyRange`; 如果需要模糊搜索, 用游标。"

---

## 复合索引与性能对比

你继续探索, 发现 IndexedDB 支持复合索引 (Compound Index)。

"如果我想按日期范围查询某个标签的笔记呢?" 你想。

你修改数据库结构, 添加了复合索引:

```javascript
request.onupgradeneeded = (event) => {
    const db = event.target.result;

    if (db.objectStoreNames.contains('notes')) {
        db.deleteObjectStore('notes');
    }

    const objectStore = db.createObjectStore('notes', {
        keyPath: 'id',
        autoIncrement: true
    });

    // 单字段索引
    objectStore.createIndex('title', 'title', { unique: false });
    objectStore.createIndex('createdAt', 'createdAt', { unique: false });
    objectStore.createIndex('tags', 'tags', {
        unique: false,
        multiEntry: true
    });

    // ✅ 复合索引: tag + 日期
    objectStore.createIndex('tagAndDate', ['tags', 'createdAt'], {
        unique: false
    });
};
```

现在你可以高效地查询 "标签为 JavaScript 且创建于最近 7 天的笔记":

```javascript
// 使用复合索引查询
async function getRecentNotesByTag(tag, days = 7) {
    const db = await openDB();
    const transaction = db.transaction(['notes'], 'readonly');
    const objectStore = transaction.objectStore('notes');
    const index = objectStore.index('tagAndDate');

    const startDate = Date.now() - days * 24 * 60 * 60 * 1000;

    // ✅ 复合索引的范围查询
    const range = IDBKeyRange.bound(
        [tag, startDate],  // 下界
        [tag, Date.now()], // 上界
        false,
        false
    );

    const request = index.getAll(range);

    return new Promise((resolve, reject) => {
        request.onsuccess = () => {
            resolve(request.result);
        };

        request.onerror = () => {
            reject(request.error);
        };
    });
}
```

你做了一个性能对比测试:

```javascript
// 性能对比测试
async function performanceTest() {
    const keyword = 'JavaScript';

    // 方法 1: getAll 后过滤
    console.time('Method 1: getAll + filter');
    await searchNotesOld(keyword);
    console.timeEnd('Method 1: getAll + filter');

    // 方法 2: 索引 + IDBKeyRange
    console.time('Method 2: Index + KeyRange');
    await searchNotesByTitle(keyword);
    console.timeEnd('Method 2: Index + KeyRange');

    // 方法 3: 游标遍历
    console.time('Method 3: Cursor');
    await searchNotesWithCursor(keyword);
    console.timeEnd('Method 3: Cursor');

    // 方法 4: 复合索引
    console.time('Method 4: Compound Index');
    await getRecentNotesByTag('JavaScript', 7);
    console.timeEnd('Method 4: Compound Index');
}
```

测试结果 (500 条笔记):

```
Method 1: getAll + filter: 2847ms
Method 2: Index + KeyRange: 12ms
Method 3: Cursor: 156ms
Method 4: Compound Index: 8ms
```

"复合索引最快!" 你惊讶地发现, "但代价是数据库体积会增加。"

---

## 事务的深度理解

下午, 你开始研究事务 (Transaction)。

你之前一直用 `readonly` 事务读取数据, 用 `readwrite` 事务写入数据, 但从没深入理解事务的机制。

你创建了一个测试场景: 批量导入笔记。

```javascript
// 批量导入笔记 (朴素实现)
async function importNotesNaive(notes) {
    const db = await openDB();

    for (const note of notes) {
        // ❌ 问题: 每次循环都创建新事务
        const transaction = db.transaction(['notes'], 'readwrite');
        const objectStore = transaction.objectStore('notes');

        await new Promise((resolve, reject) => {
            const request = objectStore.add(note);
            request.onsuccess = () => resolve();
            request.onerror = () => reject(request.error);
        });
    }
}
```

你导入 100 条笔记, 发现耗时 1.2 秒。

"为什么这么慢?" 你检查代码, 发现每次循环都创建了新事务。

"事务是有开销的, " 你意识到, "应该在一个事务中批量操作。"

你重写了导入函数:

```javascript
// 批量导入笔记 (优化版本)
async function importNotesOptimized(notes) {
    const db = await openDB();

    // ✅ 创建一个事务, 执行所有操作
    const transaction = db.transaction(['notes'], 'readwrite');
    const objectStore = transaction.objectStore('notes');

    const promises = notes.map(note => {
        return new Promise((resolve, reject) => {
            const request = objectStore.add(note);
            request.onsuccess = () => resolve(request.result);
            request.onerror = () => reject(request.error);
        });
    });

    // 等待所有操作完成
    const results = await Promise.all(promises);

    // ✅ 等待事务提交
    await new Promise((resolve, reject) => {
        transaction.oncomplete = () => resolve();
        transaction.onerror = () => reject(transaction.error);
    });

    return results;
}
```

再次测试, 导入 100 条笔记只需要 180ms!

"快了 6 倍多!" 你满意地点头。

你又测试了事务的原子性:

```javascript
// 测试事务回滚
async function testTransactionRollback() {
    const db = await openDB();

    const transaction = db.transaction(['notes'], 'readwrite');
    const objectStore = transaction.objectStore('notes');

    try {
        // 添加第一条笔记
        await new Promise((resolve, reject) => {
            const request = objectStore.add({
                title: 'Note 1',
                content: 'Content 1',
                createdAt: Date.now()
            });
            request.onsuccess = () => resolve();
            request.onerror = () => reject(request.error);
        });

        // ❌ 故意添加一条无效笔记 (缺少必需字段)
        await new Promise((resolve, reject) => {
            const request = objectStore.add({
                // 缺少 id, 但 autoIncrement 会自动生成
                // 故意传入重复的 id
            });
            request.onsuccess = () => resolve();
            request.onerror = () => reject(request.error);
        });

        // 添加第三条笔记
        await new Promise((resolve, reject) => {
            const request = objectStore.add({
                title: 'Note 3',
                content: 'Content 3',
                createdAt: Date.now()
            });
            request.onsuccess = () => resolve();
            request.onerror = () => reject(request.error);
        });

    } catch (error) {
        console.error('事务失败:', error);
        // ✅ 事务自动回滚, 所有操作都不生效
        transaction.abort();
    }
}
```

"事务要么全部成功, 要么全部失败, " 你在笔记中总结, "这保证了数据一致性。"

---

## 版本升级与数据迁移

傍晚, 你遇到了一个新问题: 版本升级。

你想给笔记增加一个新字段 `category` (分类), 但现有的 500 条笔记都没有这个字段。如何在不丢失数据的情况下迁移呢?

你研究了 IndexedDB 的版本升级机制:

```javascript
// 版本升级与数据迁移
function openDBWithMigration() {
    return new Promise((resolve, reject) => {
        // ✅ 升级到版本 3
        const request = indexedDB.open('NotesDB', 3);

        request.onupgradeneeded = (event) => {
            const db = event.target.result;
            const transaction = event.target.transaction;
            const oldVersion = event.oldVersion;
            const newVersion = event.newVersion;

            console.log(`数据库升级: v${oldVersion} → v${newVersion}`);

            // 版本 1 → 2: 添加索引
            if (oldVersion < 2) {
                const objectStore = transaction.objectStore('notes');
                objectStore.createIndex('title', 'title', { unique: false });
                objectStore.createIndex('createdAt', 'createdAt', { unique: false });
            }

            // 版本 2 → 3: 添加 category 字段
            if (oldVersion < 3) {
                const objectStore = transaction.objectStore('notes');

                // ✅ 创建 category 索引
                objectStore.createIndex('category', 'category', { unique: false });

                // ✅ 迁移现有数据: 为所有笔记添加默认 category
                const cursorRequest = objectStore.openCursor();

                cursorRequest.onsuccess = (event) => {
                    const cursor = event.target.result;

                    if (cursor) {
                        const note = cursor.value;

                        // 如果笔记没有 category, 设置默认值
                        if (!note.category) {
                            note.category = 'Uncategorized';
                            cursor.update(note);
                        }

                        cursor.continue();
                    }
                };
            }
        };

        request.onsuccess = (event) => {
            console.log('数据库升级完成');
            resolve(event.target.result);
        };

        request.onerror = (event) => {
            reject(event.target.error);
        };
    });
}
```

你测试升级流程, 发现浏览器自动处理了版本升级, 所有旧数据都保留了, 并且被添加了新字段。

"这个机制很优雅, " 你想, "类似于数据库的 schema migration。"

你又实现了一个更复杂的迁移场景: 重命名字段。

```javascript
// 复杂迁移: 重命名字段
request.onupgradeneeded = (event) => {
    const db = event.target.result;
    const transaction = event.target.transaction;
    const oldVersion = event.oldVersion;

    // 版本 3 → 4: 将 createdAt 重命名为 createdTime
    if (oldVersion < 4) {
        const objectStore = transaction.objectStore('notes');

        // ✅ 步骤 1: 删除旧索引
        if (objectStore.indexNames.contains('createdAt')) {
            objectStore.deleteIndex('createdAt');
        }

        // ✅ 步骤 2: 创建新索引
        objectStore.createIndex('createdTime', 'createdTime', { unique: false });

        // ✅ 步骤 3: 迁移数据
        const cursorRequest = objectStore.openCursor();

        cursorRequest.onsuccess = (event) => {
            const cursor = event.target.result;

            if (cursor) {
                const note = cursor.value;

                // 重命名字段
                if (note.createdAt !== undefined) {
                    note.createdTime = note.createdAt;
                    delete note.createdAt;
                    cursor.update(note);
                }

                cursor.continue();
            }
        };
    }
};
```

---

## 性能优化的总结

晚上 8 点, 你关上笔记本, 整理了一天的收获。

你创建了一个性能优化清单:

```markdown
# IndexedDB 性能优化清单

## 1. 索引策略
- ✅ 为常用查询字段创建索引
- ✅ 使用 multiEntry 索引处理数组字段
- ✅ 创建复合索引加速多条件查询
- ⚠️ 索引会增加存储空间和写入开销

## 2. 查询优化
- ✅ 优先使用 IDBKeyRange (最快)
- ✅ 避免 getAll() 后过滤 (最慢)
- ✅ 游标适合复杂过滤逻辑
- ✅ 使用 count() 而非 getAll().length

## 3. 事务管理
- ✅ 批量操作放在一个事务中
- ✅ 尽快完成事务 (避免长时间锁定)
- ✅ 只读事务优先使用 readonly 模式
- ✅ 监听 transaction.oncomplete 确保提交

## 4. 版本升级
- ✅ 只在 onupgradeneeded 中修改 schema
- ✅ 使用游标迁移现有数据
- ✅ 版本号递增, 不能回退
- ✅ 测试升级流程的向后兼容性

## 5. 数据设计
- ✅ 合理的主键设计 (autoIncrement 或自定义)
- ✅ 避免存储超大对象 (拆分存储)
- ✅ 考虑索引膨胀问题
- ✅ 定期清理过期数据
```

你看着性能对比数据, 满意地笑了:

**优化前**:
- 搜索 500 条笔记: 2847ms
- 批量导入 100 条笔记: 1200ms

**优化后**:
- 使用索引搜索: 12ms (快 237 倍)
- 使用复合索引: 8ms (快 355 倍)
- 批量导入: 180ms (快 6.7 倍)

"这些优化让应用体验提升了几个数量级, " 你在笔记中总结。

明天, 你打算继续优化应用的其他部分。但今天的收获已经足够丰富了——你不仅解决了性能问题, 还深入理解了 IndexedDB 的高级特性。

---

## 知识档案: IndexedDB 高级特性的八个核心机制

**规则 1: 索引加速查询, 但会增加写入成本和存储空间**

索引类似于数据库的 B-Tree 索引, 为特定字段创建快速查找结构。

```javascript
// 创建索引
const objectStore = db.createObjectStore('notes', { keyPath: 'id' });

// 单字段索引
objectStore.createIndex('title', 'title', { unique: false });

// 复合索引: 多个字段组合
objectStore.createIndex('tagAndDate', ['tags', 'createdAt'], {
    unique: false
});

// 数组字段索引: multiEntry
objectStore.createIndex('tags', 'tags', {
    unique: false,
    multiEntry: true  // 为数组中每个元素创建索引条目
});

// 唯一索引: 保证字段值唯一
objectStore.createIndex('email', 'email', { unique: true });
```

索引的开销:
- **写入性能**: 每次写入需要更新所有索引 (额外 20-50% 开销)
- **存储空间**: 每个索引占用额外存储 (约原始数据的 10-30%)
- **查询性能**: 索引查询比全表扫描快 10-100 倍

索引选择原则:
- **常用查询字段**: 为高频查询字段创建索引
- **组合查询**: 复合索引覆盖多条件查询
- **避免过度索引**: 每个索引都有维护成本
- **唯一性约束**: 需要唯一性时使用 unique 索引

---

**规则 2: IDBKeyRange 提供高效的范围查询能力**

IDBKeyRange 定义索引查询范围, 性能远优于全表扫描。

```javascript
// IDBKeyRange 的四种创建方式

// 1. only: 精确匹配
const exactRange = IDBKeyRange.only('JavaScript');
// 查询 tag === 'JavaScript'

// 2. lowerBound: 下界查询
const lowerRange = IDBKeyRange.lowerBound(1000000, false);
// 查询 createdAt >= 1000000 (false 表示包含边界)

const lowerRangeExclusive = IDBKeyRange.lowerBound(1000000, true);
// 查询 createdAt > 1000000 (true 表示不包含边界)

// 3. upperBound: 上界查询
const upperRange = IDBKeyRange.upperBound(2000000, false);
// 查询 createdAt <= 2000000

// 4. bound: 范围查询
const rangeQuery = IDBKeyRange.bound(
    1000000,  // 下界
    2000000,  // 上界
    false,    // 包含下界
    false     // 包含上界
);
// 查询 1000000 <= createdAt <= 2000000

// 使用 KeyRange 查询
const index = objectStore.index('createdAt');
const request = index.getAll(rangeQuery);

request.onsuccess = () => {
    const results = request.result;
    console.log(`找到 ${results.length} 条记录`);
};
```

字符串前缀匹配:
```javascript
// 前缀匹配: 查询以 "Java" 开头的标题
const keyword = 'Java';
const prefixRange = IDBKeyRange.bound(
    keyword,
    keyword + '\uffff',  // Unicode 最大字符
    false,
    false
);

const index = objectStore.index('title');
const request = index.getAll(prefixRange);
// 匹配: "Java", "JavaScript", "Java Tutorial"
```

复合索引的范围查询:
```javascript
// 复合索引: ['category', 'createdAt']
const categoryAndDateRange = IDBKeyRange.bound(
    ['Work', 1000000],     // category === 'Work' AND createdAt >= 1000000
    ['Work', Date.now()],  // category === 'Work' AND createdAt <= now
    false,
    false
);
```

性能对比:
- **getAll() + filter**: O(n) - 扫描所有记录
- **IDBKeyRange**: O(log n + k) - 索引查找 + 结果集大小
- **精确匹配 (only)**: O(log n) - 最快

---

**规则 3: 游标提供灵活的遍历和过滤能力**

游标 (Cursor) 是 IndexedDB 的迭代器, 适合复杂过滤和数据处理。

```javascript
// 基础游标遍历
const request = objectStore.openCursor();

request.onsuccess = (event) => {
    const cursor = event.target.result;

    if (cursor) {
        console.log('当前记录:', cursor.value);
        console.log('当前主键:', cursor.key);

        // 移动到下一条记录
        cursor.continue();
    } else {
        console.log('遍历完成');
    }
};

// 带方向的游标
const request = objectStore.openCursor(null, 'prev');  // 逆序遍历
// 方向选项: 'next', 'nextunique', 'prev', 'prevunique'

// 索引游标
const index = objectStore.index('createdAt');
const request = index.openCursor();  // 按 createdAt 顺序遍历

// 带范围的游标
const range = IDBKeyRange.lowerBound(1000000);
const request = objectStore.openCursor(range);  // 只遍历符合范围的记录
```

游标的高级操作:
```javascript
// 更新当前记录
cursor.onsuccess = (event) => {
    const cursor = event.target.result;

    if (cursor) {
        const note = cursor.value;

        // 修改记录
        note.views = (note.views || 0) + 1;

        // ✅ 更新当前记录
        const updateRequest = cursor.update(note);

        updateRequest.onsuccess = () => {
            console.log('记录已更新');
        };

        cursor.continue();
    }
};

// 删除当前记录
cursor.onsuccess = (event) => {
    const cursor = event.target.result;

    if (cursor) {
        if (cursor.value.expired) {
            // ✅ 删除当前记录
            cursor.delete();
        }

        cursor.continue();
    }
};

// 跳过记录: advance
cursor.advance(10);  // 跳过 10 条记录
cursor.continue(key);  // 跳到指定主键
```

游标 vs getAll:
- **内存占用**: 游标逐条处理, getAll 一次加载全部
- **性能**: getAll 更快 (批量读取), 游标更灵活
- **适用场景**:
  - getAll: 数据量小 (<1000 条), 需要全部数据
  - 游标: 数据量大, 需要过滤/更新/删除操作

---

**规则 4: 事务保证原子性, 批量操作必须在同一事务中**

事务 (Transaction) 是 IndexedDB 的核心机制, 保证数据一致性。

```javascript
// 创建事务
const transaction = db.transaction(['notes', 'tags'], 'readwrite');
// 参数 1: 对象仓库列表
// 参数 2: 模式 'readonly' | 'readwrite' | 'versionchange'

const objectStore = transaction.objectStore('notes');

// 事务自动提交
transaction.oncomplete = () => {
    console.log('事务提交成功');
};

transaction.onerror = () => {
    console.error('事务失败, 已回滚');
};

transaction.onabort = () => {
    console.log('事务被中止');
};
```

批量操作模式:
```javascript
// ❌ 错误: 每次循环创建新事务 (慢)
for (const note of notes) {
    const transaction = db.transaction(['notes'], 'readwrite');
    const objectStore = transaction.objectStore('notes');
    await objectStore.add(note);
}
// 100 条记录: 1200ms

// ✅ 正确: 一个事务批量操作 (快)
const transaction = db.transaction(['notes'], 'readwrite');
const objectStore = transaction.objectStore('notes');

for (const note of notes) {
    objectStore.add(note);  // 不需要 await
}

await new Promise((resolve, reject) => {
    transaction.oncomplete = resolve;
    transaction.onerror = reject;
});
// 100 条记录: 180ms (快 6.7 倍)
```

事务的原子性:
```javascript
// 事务中的所有操作要么全部成功, 要么全部失败
const transaction = db.transaction(['notes'], 'readwrite');
const objectStore = transaction.objectStore('notes');

try {
    objectStore.add({ title: 'Note 1', ... });
    objectStore.add({ title: 'Note 2', ... });
    objectStore.add({ title: 'Note 3', ... });

    // 如果任一操作失败, 整个事务回滚
} catch (error) {
    transaction.abort();  // 手动中止事务
}
```

事务的生命周期:
- **Active**: 事务正在执行操作
- **Inactive**: 操作完成, 等待提交 (不能再添加操作)
- **Committing**: 正在提交到磁盘
- **Completed**: 提交成功
- **Aborted**: 事务失败或被中止

事务最佳实践:
- **最小作用域**: 只包含必要的对象仓库
- **快速完成**: 避免在事务中执行耗时操作 (如网络请求)
- **错误处理**: 监听 onerror, 处理失败情况
- **批量优化**: 多个操作合并到一个事务

---

**规则 5: 版本升级机制支持 schema 变更和数据迁移**

IndexedDB 的版本升级类似于数据库的 schema migration。

```javascript
// 版本升级
const request = indexedDB.open('MyDB', 3);  // 版本号必须递增

request.onupgradeneeded = (event) => {
    const db = event.target.result;
    const transaction = event.target.transaction;
    const oldVersion = event.oldVersion;
    const newVersion = event.newVersion;

    console.log(`升级: v${oldVersion} → v${newVersion}`);

    // ✅ 只在 onupgradeneeded 中修改 schema

    // 版本 1: 初始创建
    if (oldVersion < 1) {
        const objectStore = db.createObjectStore('notes', {
            keyPath: 'id',
            autoIncrement: true
        });

        objectStore.createIndex('title', 'title');
    }

    // 版本 2: 添加索引
    if (oldVersion < 2) {
        const objectStore = transaction.objectStore('notes');
        objectStore.createIndex('createdAt', 'createdAt');
    }

    // 版本 3: 添加字段并迁移数据
    if (oldVersion < 3) {
        const objectStore = transaction.objectStore('notes');

        // 创建新索引
        objectStore.createIndex('category', 'category');

        // ✅ 迁移现有数据
        const cursorRequest = objectStore.openCursor();

        cursorRequest.onsuccess = (event) => {
            const cursor = event.target.result;

            if (cursor) {
                const note = cursor.value;

                // 为旧数据添加新字段
                if (!note.category) {
                    note.category = 'Uncategorized';
                    cursor.update(note);
                }

                cursor.continue();
            }
        };
    }
};

request.onsuccess = (event) => {
    const db = event.target.result;
    console.log('数据库版本:', db.version);
};
```

删除和重命名对象仓库:
```javascript
request.onupgradeneeded = (event) => {
    const db = event.target.result;

    // 删除对象仓库
    if (db.objectStoreNames.contains('oldStore')) {
        db.deleteObjectStore('oldStore');
    }

    // 重命名对象仓库 (分两步)
    if (db.objectStoreNames.contains('notes')) {
        // 1. 创建新对象仓库
        const newStore = db.createObjectStore('articles', { keyPath: 'id' });

        // 2. 迁移数据
        const oldStore = event.target.transaction.objectStore('notes');
        const cursorRequest = oldStore.openCursor();

        cursorRequest.onsuccess = (event) => {
            const cursor = event.target.result;

            if (cursor) {
                newStore.add(cursor.value);
                cursor.continue();
            }
        };

        // 3. 删除旧对象仓库 (迁移完成后)
        // 注意: 不能在 onupgradeneeded 中立即删除, 需要在新版本中删除
    }
};
```

版本升级规则:
- **版本号递增**: 必须大于当前版本
- **唯一时机**: 只能在 onupgradeneeded 中修改 schema
- **事务环境**: onupgradeneeded 在 versionchange 事务中执行
- **向后兼容**: 旧版本数据必须能在新版本中使用

数据迁移最佳实践:
- **增量升级**: 每个版本只做必要的改动
- **测试覆盖**: 测试从任意旧版本升级到新版本
- **数据备份**: 升级前导出数据 (可选)
- **渐进部署**: 分阶段发布版本升级

---

**规则 6: multiEntry 索引支持数组字段的独立查询**

multiEntry 索引为数组中的每个元素创建独立索引条目。

```javascript
// 创建 multiEntry 索引
const objectStore = db.createObjectStore('notes', { keyPath: 'id' });

objectStore.createIndex('tags', 'tags', {
    unique: false,
    multiEntry: true  // ✅ 数组索引
});

// 数据示例
const note = {
    id: 1,
    title: 'IndexedDB Tutorial',
    tags: ['JavaScript', 'IndexedDB', 'Storage']
};

objectStore.add(note);
```

multiEntry 索引的查询:
```javascript
// 查询包含特定 tag 的所有笔记
const index = objectStore.index('tags');
const request = index.getAll('JavaScript');

request.onsuccess = () => {
    const results = request.result;
    // 返回所有 tags 包含 'JavaScript' 的笔记
};

// 普通索引 vs multiEntry 索引
const normalIndex = objectStore.index('category');
normalIndex.get('Work');  // 查询 category === 'Work'

const multiIndex = objectStore.index('tags');
multiIndex.get('JavaScript');  // 查询 tags 包含 'JavaScript'
```

multiEntry 索引的实现原理:
```javascript
// 数据: { id: 1, tags: ['A', 'B', 'C'] }

// multiEntry 索引结构:
// 'A' → [1]
// 'B' → [1]
// 'C' → [1]

// 普通索引结构:
// ['A', 'B', 'C'] → [1]  (整个数组作为一个键)
```

multiEntry 索引的开销:
- **存储空间**: 数组长度 × 索引开销
- **写入性能**: 每个数组元素都需要更新索引
- **查询性能**: 单个元素查询很快 (O(log n))

使用场景:
- **标签系统**: 按标签查询笔记/文章
- **分类系统**: 一个项目属于多个分类
- **权限系统**: 一个用户有多个角色

---

**规则 7: 复合索引支持多字段组合查询**

复合索引 (Compound Index) 将多个字段组合成一个索引。

```javascript
// 创建复合索引
const objectStore = db.createObjectStore('notes', { keyPath: 'id' });

// ✅ 复合索引: category + createdAt
objectStore.createIndex('categoryAndDate', ['category', 'createdAt'], {
    unique: false
});

// ✅ 复合索引: author + status + priority
objectStore.createIndex('authorStatusPriority', ['author', 'status', 'priority'], {
    unique: false
});
```

复合索引的查询:
```javascript
// 精确匹配所有字段
const index = objectStore.index('categoryAndDate');
const request = index.get(['Work', 1704038400000]);
// 查询 category === 'Work' AND createdAt === 1704038400000

// 范围查询
const range = IDBKeyRange.bound(
    ['Work', 1704038400000],  // 下界
    ['Work', 1704067200000],  // 上界
    false,
    false
);

const request = index.getAll(range);
// 查询 category === 'Work' AND 1704038400000 <= createdAt <= 1704067200000
```

复合索引的前缀匹配:
```javascript
// 复合索引: ['category', 'status', 'priority']

// ✅ 可以使用的查询
index.get(['Work']);                      // category === 'Work'
index.get(['Work', 'Active']);           // category === 'Work' AND status === 'Active'
index.get(['Work', 'Active', 'High']);   // 所有字段匹配

// ❌ 不能跳过前面的字段
index.get([undefined, 'Active']);         // 无效
index.get([undefined, undefined, 'High']); // 无效
```

复合索引 vs 多个单字段索引:
```javascript
// 方案 1: 多个单字段索引
objectStore.createIndex('category', 'category');
objectStore.createIndex('status', 'status');

// 查询 category === 'Work' AND status === 'Active'
// ❌ 需要分两步查询, 然后手动过滤
const categoryIndex = objectStore.index('category');
const results = await categoryIndex.getAll('Work');
const filtered = results.filter(note => note.status === 'Active');

// 方案 2: 复合索引
objectStore.createIndex('categoryAndStatus', ['category', 'status']);

// ✅ 一步查询, 性能更好
const index = objectStore.index('categoryAndStatus');
const results = await index.getAll(['Work', 'Active']);
```

复合索引的设计原则:
- **查询频率**: 为高频组合查询创建复合索引
- **字段顺序**: 选择性高的字段放前面 (区分度大的字段)
- **前缀利用**: 考虑前缀查询的需求
- **索引数量**: 避免创建过多复合索引 (维护成本高)

---

**规则 8: 性能优化需要权衡查询速度、写入成本和存储空间**

IndexedDB 性能优化是多维度权衡的结果。

```javascript
// 性能优化决策树

// 场景 1: 高频精确查询
// 数据: 1000 条笔记, 每秒 10 次按 title 查询
// 优化: 创建 title 索引
objectStore.createIndex('title', 'title');
// 查询性能: 2847ms → 12ms (快 237 倍)
// 代价: 写入慢 20%, 存储增加 10%

// 场景 2: 复杂条件查询
// 数据: 5000 条笔记, 按 category + 日期范围查询
// 优化: 创建复合索引
objectStore.createIndex('categoryAndDate', ['category', 'createdAt']);
// 查询性能: 4523ms → 8ms (快 565 倍)
// 代价: 写入慢 30%, 存储增加 15%

// 场景 3: 批量导入
// 数据: 一次导入 1000 条笔记
// 优化: 使用单个事务批量操作
const transaction = db.transaction(['notes'], 'readwrite');
for (const note of notes) {
    transaction.objectStore('notes').add(note);
}
// 性能: 12000ms → 1800ms (快 6.7 倍)

// 场景 4: 大数据量遍历
// 数据: 10000 条笔记, 需要更新所有记录
// 优化: 使用游标逐条处理 (避免内存溢出)
const cursor = objectStore.openCursor();
cursor.onsuccess = (event) => {
    const cursor = event.target.result;
    if (cursor) {
        // 处理当前记录
        const note = cursor.value;
        note.processed = true;
        cursor.update(note);
        cursor.continue();
    }
};
// 内存占用: 500MB → 50MB (节省 90%)
```

性能优化清单:

**查询优化**:
- ✅ 为高频查询字段创建索引 (10-1000 倍提升)
- ✅ 使用 IDBKeyRange 代替 getAll + filter (100+ 倍提升)
- ✅ 复合索引覆盖多条件查询 (避免多次查询)
- ✅ count() 代替 getAll().length (避免数据传输)
- ❌ 避免在主线程执行耗时查询 (考虑 Web Worker)

**写入优化**:
- ✅ 批量操作放在一个事务中 (5-10 倍提升)
- ✅ 控制索引数量 (每个索引增加 20-50% 写入成本)
- ✅ 使用 readonly 事务读取 (减少锁竞争)
- ❌ 避免频繁的小事务 (事务有固定开销)

**存储优化**:
- ✅ 定期清理过期数据 (reduce 存储压力)
- ✅ 拆分超大对象 (单个对象 <1MB)
- ✅ 压缩文本数据 (JSON → 压缩字符串)
- ⚠️ 索引占用 10-30% 额外空间

**内存优化**:
- ✅ 游标遍历代替 getAll (大数据集)
- ✅ 分页查询 (limit + offset 模式)
- ✅ 及时关闭数据库连接 (db.close())

性能监控指标:
```javascript
// 查询性能监控
console.time('Query: searchNotes');
const results = await searchNotes('JavaScript');
console.timeEnd('Query: searchNotes');
// Query: searchNotes: 12ms

// 事务性能监控
const transaction = db.transaction(['notes'], 'readwrite');
const startTime = performance.now();

transaction.oncomplete = () => {
    const duration = performance.now() - startTime;
    console.log(`事务耗时: ${duration.toFixed(2)}ms`);
};

// 存储空间监控
if (navigator.storage && navigator.storage.estimate) {
    const estimate = await navigator.storage.estimate();
    console.log(`已用: ${(estimate.usage / 1024 / 1024).toFixed(2)}MB`);
    console.log(`可用: ${(estimate.quota / 1024 / 1024).toFixed(2)}MB`);
    console.log(`使用率: ${(estimate.usage / estimate.quota * 100).toFixed(2)}%`);
}
```

优化决策矩阵:

| 场景 | 查询频率 | 数据量 | 推荐方案 | 性能提升 | 代价 |
|------|---------|--------|---------|---------|-----|
| 用户搜索 | 高 | 中 (1K-10K) | 单字段索引 | 100-500x | 写入慢 20% |
| 多条件筛选 | 中 | 大 (10K-100K) | 复合索引 | 200-1000x | 写入慢 30% |
| 标签查询 | 高 | 中 | multiEntry 索引 | 50-200x | 写入慢 40% |
| 批量导入 | 低 | 大 | 单事务批量 | 5-10x | 无 |
| 全表更新 | 低 | 大 | 游标遍历 | 内存节省 90% | 时间稍慢 |
| 简单查询 | 低 | 小 (<1K) | 无索引 | 无需优化 | 无 |

---

**事故档案编号**: NETWORK-2024-1958
**影响范围**: IndexedDB 高级特性、索引优化、事务管理、版本升级、性能优化
**根本原因**: 缺乏对 IndexedDB 高级特性的理解导致性能问题, 全表扫描代替索引查询, 事务使用不当
**学习成本**: 中高 (需理解数据库索引原理、事务机制、版本管理策略)

这是 JavaScript 世界第 158 次被记录的网络与数据事故。索引加速查询但增加写入成本和存储空间, 需要权衡查询频率和数据量选择合适的索引策略。IDBKeyRange 提供高效的范围查询能力, 性能远优于全表扫描后过滤。游标提供灵活的遍历和过滤能力, 适合大数据集和复杂处理逻辑。事务保证原子性, 批量操作必须在同一事务中以获得最佳性能。版本升级机制支持 schema 变更和数据迁移, 类似于数据库的 migration 系统。multiEntry 索引支持数组字段的独立查询, 为每个数组元素创建索引条目。复合索引支持多字段组合查询, 避免多次查询和手动过滤。性能优化需要权衡查询速度、写入成本和存储空间, 根据实际场景选择合适的优化策略。理解 IndexedDB 的高级特性和优化技巧是构建高性能离线应用的基础。

---
