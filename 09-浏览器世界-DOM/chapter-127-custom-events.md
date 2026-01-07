《第 127 次记录：创造新的因果 —— 当浏览器的事件不够用时》

## 组件通信难题

周二下午 3 点 42 分，你正在重构一个复杂的数据看板页面。

页面包含多个独立组件：图表组件、筛选器组件、数据表格组件、导出按钮组件。产品需求是："点击筛选器时，图表和表格要同步更新；点击图表的某个数据点，筛选器要高亮对应条件；点击导出按钮，要获取当前筛选后的数据。" 简单来说，这些组件需要互相通信。

你最初的实现是直接调用组件的方法：

```javascript
class FilterPanel {
  constructor() {
    this.filters = {};
  }

  updateFilter(key, value) {
    this.filters[key] = value;

    // ❌ 直接调用其他组件的方法
    chart.refresh(this.filters);
    table.refresh(this.filters);
    exportButton.updateData(this.filters);
  }
}

class Chart {
  refresh(filters) {
    // 重新渲染图表
  }

  selectDataPoint(point) {
    // ❌ 直接调用筛选器的方法
    filterPanel.highlightFilter(point.category);
  }
}
```

测试了几天后，你发现这种实现有严重问题：
1. 组件之间强耦合，`FilterPanel` 必须知道 `chart`、`table`、`exportButton` 的存在
2. 新增一个组件（比如统计摘要），需要修改 `FilterPanel` 的代码
3. 组件无法复用，因为它们依赖于具体的其他组件实例

前端架构师老李看了你的代码，摇头说："这是典型的强耦合。用自定义事件重构吧，让组件通过事件通信，而不是直接调用。"

"自定义事件？" 你问。

"对，" 老李说，"就像 click、submit 是浏览器预定义的事件，你也可以创建自己的事件，比如 'filterChanged'、'dataPointSelected'。组件发出事件，其他组件监听事件，彼此不需要知道对方的存在。"

## 第一次尝试

老李给你展示了 `CustomEvent` 的基本用法：

```javascript
// 创建自定义事件
const event = new CustomEvent('filterChanged', {
  detail: { category: 'sales', value: 'Q1' }, // 自定义数据
  bubbles: true,    // 是否冒泡
  cancelable: true  // 是否可取消
});

// 派发事件
element.dispatchEvent(event);

// 监听事件
element.addEventListener('filterChanged', (event) => {
  console.log('筛选条件变化:', event.detail);
});
```

你决定用自定义事件重构组件通信。首先改造 `FilterPanel`：

```javascript
class FilterPanel {
  constructor(element) {
    this.element = element;
    this.filters = {};
  }

  updateFilter(key, value) {
    this.filters[key] = value;

    // 派发自定义事件
    const event = new CustomEvent('filterChanged', {
      detail: { filters: this.filters },
      bubbles: true
    });

    this.element.dispatchEvent(event);
  }
}
```

然后改造其他组件，让它们监听事件：

```javascript
class Chart {
  constructor(element) {
    this.element = element;

    // 监听筛选变化
    document.addEventListener('filterChanged', (event) => {
      this.refresh(event.detail.filters);
    });
  }

  refresh(filters) {
    console.log('图表更新:', filters);
    // 重新渲染图表
  }

  selectDataPoint(point) {
    // 派发数据点选中事件
    const event = new CustomEvent('dataPointSelected', {
      detail: { point },
      bubbles: true
    });

    this.element.dispatchEvent(event);
  }
}

class DataTable {
  constructor(element) {
    this.element = element;

    // 监听筛选变化
    document.addEventListener('filterChanged', (event) => {
      this.refresh(event.detail.filters);
    });
  }

  refresh(filters) {
    console.log('表格更新:', filters);
    // 重新渲染表格
  }
}

class ExportButton {
  constructor(element) {
    this.element = element;
    this.currentFilters = {};

    // 监听筛选变化
    document.addEventListener('filterChanged', (event) => {
      this.currentFilters = event.detail.filters;
    });

    // 点击导出
    element.addEventListener('click', () => {
      this.export(this.currentFilters);
    });
  }

  export(filters) {
    console.log('导出数据:', filters);
    // 导出逻辑
  }
}
```

你测试了一下：
- 点击筛选器 → 图表和表格同时更新 ✅
- 点击图表数据点 → 可以派发事件 ✅
- 点击导出按钮 → 获取到当前筛选条件 ✅

"太棒了！" 你兴奋地说，"组件之间完全解耦了，`FilterPanel` 不需要知道有哪些组件在监听它的事件。"

老李点头："这就是发布-订阅模式的威力。"

## 事件冒泡的应用

你注意到一个细节：所有组件都在 `document` 上监听事件，而不是在具体的元素上。你问老李为什么。

"因为自定义事件可以冒泡，" 老李解释道，"如果你在组件元素上派发事件，并设置 `bubbles: true`，事件会冒泡到 `document`。这样所有组件都可以在 `document` 上统一监听。"

你做了一个实验：

```javascript
const filterPanel = document.querySelector('.filter-panel');

// 在 filterPanel 上派发事件
const event = new CustomEvent('test', {
  detail: { message: 'hello' },
  bubbles: true // 冒泡
});

filterPanel.dispatchEvent(event);

// 在不同层级监听
filterPanel.addEventListener('test', () => {
  console.log('在 filterPanel 上监听到');
});

document.body.addEventListener('test', () => {
  console.log('在 body 上监听到');
});

document.addEventListener('test', () => {
  console.log('在 document 上监听到');
});

// 输出:
// 在 filterPanel 上监听到
// 在 body 上监听到
// 在 document 上监听到
```

"冒泡让事件可以被更高层级的元素监听到，" 老李说，"这对事件总线模式很有用。"

你实现了一个简单的事件总线：

```javascript
class EventBus {
  constructor() {
    this.bus = document.createElement('div'); // 创建一个隐藏元素作为事件总线
  }

  // 派发事件
  emit(eventName, data) {
    const event = new CustomEvent(eventName, {
      detail: data
    });
    this.bus.dispatchEvent(event);
  }

  // 监听事件
  on(eventName, callback) {
    this.bus.addEventListener(eventName, (event) => {
      callback(event.detail);
    });
  }

  // 移除监听
  off(eventName, callback) {
    this.bus.removeEventListener(eventName, callback);
  }
}

// 使用事件总线
const eventBus = new EventBus();

// 组件 A 派发事件
eventBus.emit('userLogin', { userId: 123, username: 'alice' });

// 组件 B 监听事件
eventBus.on('userLogin', (data) => {
  console.log('用户登录:', data);
});
```

"这样所有组件都通过事件总线通信，" 老李说，"完全解耦，非常适合复杂应用。"

## 事件参数的传递

你开始探索 `CustomEvent` 的参数。老李展示了一个完整的例子：

```javascript
const button = document.querySelector('button');

// 创建带有详细参数的自定义事件
const event = new CustomEvent('buttonAction', {
  detail: {
    action: 'save',
    data: { id: 123, name: 'Product' },
    timestamp: Date.now()
  },
  bubbles: true,      // 是否冒泡
  cancelable: true,   // 是否可取消
  composed: false     // 是否穿透 Shadow DOM
});

button.dispatchEvent(event);

// 监听事件
button.addEventListener('buttonAction', (event) => {
  console.log('事件类型:', event.type);           // 'buttonAction'
  console.log('自定义数据:', event.detail);        // { action: 'save', ... }
  console.log('是否冒泡:', event.bubbles);         // true
  console.log('是否可取消:', event.cancelable);    // true
  console.log('事件目标:', event.target);          // button 元素
  console.log('时间戳:', event.timeStamp);         // DOMHighResTimeStamp
});
```

"注意 `detail` 属性，" 老李说，"这是传递自定义数据的标准方式。你可以在 `detail` 里放任何 JavaScript 值：对象、数组、函数都可以。"

你测试了更复杂的数据传递：

```javascript
// 传递复杂对象
const event = new CustomEvent('dataLoaded', {
  detail: {
    data: [
      { id: 1, name: 'Item 1' },
      { id: 2, name: 'Item 2' }
    ],
    meta: {
      total: 100,
      page: 1,
      pageSize: 20
    },
    callback: (item) => {
      console.log('处理:', item);
    }
  }
});

element.dispatchEvent(event);

// 监听并使用数据
element.addEventListener('dataLoaded', (event) => {
  const { data, meta, callback } = event.detail;

  console.log(`加载了 ${data.length} 条数据，共 ${meta.total} 条`);

  data.forEach(item => {
    callback(item); // 调用回调函数
  });
});
```

## 可取消的自定义事件

老李展示了 `cancelable` 参数的用法：

```javascript
class Form {
  constructor(element) {
    this.element = element;

    element.addEventListener('submit', (event) => {
      event.preventDefault();

      // 派发自定义的 beforeSubmit 事件
      const beforeSubmitEvent = new CustomEvent('beforeSubmit', {
        detail: { formData: new FormData(element) },
        cancelable: true // 允许取消
      });

      const allowed = this.element.dispatchEvent(beforeSubmitEvent);

      if (!allowed) {
        console.log('提交被取消');
        return;
      }

      // 继续提交
      this.submit();
    });
  }

  submit() {
    console.log('表单提交中...');
  }
}

// 监听 beforeSubmit 事件
const form = document.querySelector('form');

form.addEventListener('beforeSubmit', (event) => {
  const formData = event.detail.formData;

  // 验证表单
  const username = formData.get('username');
  if (!username) {
    alert('用户名不能为空');
    event.preventDefault(); // 取消提交
  }
});
```

你测试了一下：填写表单但不填用户名，点击提交，弹出提示"用户名不能为空"，表单没有提交。填写用户名后，表单正常提交。

"这就像浏览器的原生事件一样，" 老李说，"你可以在事件监听器里调用 `preventDefault()` 来取消操作。`dispatchEvent` 会返回布尔值：如果事件被取消，返回 `false`；否则返回 `true`。"

## 旧式事件创建方法

老李提醒道："除了 `CustomEvent`，还有一个旧的 `Event` 构造函数，但它不支持 `detail` 参数。"

```javascript
// 旧方式：Event 构造函数
const event1 = new Event('myEvent', {
  bubbles: true,
  cancelable: true
});
// ❌ 无法传递自定义数据

// 新方式：CustomEvent 构造函数
const event2 = new CustomEvent('myEvent', {
  detail: { message: 'hello' }, // ✅ 可以传递数据
  bubbles: true,
  cancelable: true
});

// 更旧的方式：createEvent + initCustomEvent（已废弃）
const event3 = document.createEvent('CustomEvent');
event3.initCustomEvent('myEvent', true, true, { message: 'hello' });
// ⚠️ 已废弃，不推荐使用
```

"永远使用 `CustomEvent`，" 老李建议，"它是现代标准，支持自定义数据传递。"

## 实际应用场景

老李展示了几个实际应用场景：

```javascript
// 场景 1: 模块加载完成通知
class Module {
  constructor() {
    this.load().then(() => {
      const event = new CustomEvent('moduleLoaded', {
        detail: { moduleName: 'UserModule' },
        bubbles: true
      });
      document.dispatchEvent(event);
    });
  }

  async load() {
    // 加载逻辑
  }
}

// 场景 2: 购物车更新通知
class ShoppingCart {
  addItem(item) {
    this.items.push(item);

    const event = new CustomEvent('cartUpdated', {
      detail: {
        items: this.items,
        total: this.getTotal()
      },
      bubbles: true
    });

    document.dispatchEvent(event);
  }
}

// 场景 3: 页面跳转前确认
class Router {
  navigate(path) {
    const event = new CustomEvent('beforeNavigate', {
      detail: { from: this.currentPath, to: path },
      cancelable: true
    });

    const allowed = document.dispatchEvent(event);

    if (!allowed) {
      console.log('导航被取消');
      return;
    }

    // 执行导航
    this.currentPath = path;
  }
}

// 场景 4: 数据同步通知
class DataSync {
  sync() {
    fetch('/api/sync')
      .then(response => response.json())
      .then(data => {
        const event = new CustomEvent('dataSynced', {
          detail: {
            data,
            syncTime: new Date()
          }
        });
        document.dispatchEvent(event);
      });
  }
}

// 统一监听所有业务事件
document.addEventListener('moduleLoaded', (event) => {
  console.log('模块加载:', event.detail.moduleName);
});

document.addEventListener('cartUpdated', (event) => {
  updateCartBadge(event.detail.items.length);
});

document.addEventListener('beforeNavigate', (event) => {
  if (hasUnsavedChanges()) {
    if (!confirm('有未保存的更改，确定离开？')) {
      event.preventDefault();
    }
  }
});

document.addEventListener('dataSynced', (event) => {
  showNotification('数据已同步');
});
```

下午 6 点，你完成了整个数据看板的重构。所有组件通过自定义事件通信，代码清晰、解耦、易于扩展。你给团队发了一封邮件："数据看板重构完成，使用自定义事件实现组件通信，新增组件只需监听对应事件，无需修改现有代码。"

## 自定义事件法则

**规则 1: 使用 CustomEvent 创建自定义事件**

`CustomEvent` 构造函数是创建自定义事件的标准方式，支持通过 `detail` 属性传递任意自定义数据。避免使用旧的 `Event` 构造函数或已废弃的 `createEvent` 方法。

```javascript
// ✅ 推荐：CustomEvent 构造函数
const event = new CustomEvent('myEvent', {
  detail: { message: 'hello', data: [1, 2, 3] }, // 自定义数据
  bubbles: true,      // 是否冒泡
  cancelable: true,   // 是否可取消
  composed: false     // 是否穿透 Shadow DOM
});

element.dispatchEvent(event);

// 监听事件
element.addEventListener('myEvent', (event) => {
  console.log(event.detail); // { message: 'hello', data: [1, 2, 3] }
});

// ❌ 不推荐：Event 构造函数（无法传递 detail）
const oldEvent = new Event('myEvent');
// 无法传递自定义数据

// ❌ 已废弃：createEvent + initCustomEvent
const deprecatedEvent = document.createEvent('CustomEvent');
deprecatedEvent.initCustomEvent('myEvent', true, true, { data: 'hello' });
// 已废弃，不推荐使用
```

**规则 2: 自定义数据通过 detail 属性传递**

`detail` 属性是传递自定义数据的标准方式，可以包含任意 JavaScript 值：对象、数组、函数等。监听器通过 `event.detail` 访问这些数据。

```javascript
// 传递复杂数据结构
const event = new CustomEvent('dataLoaded', {
  detail: {
    items: [{ id: 1, name: 'Item 1' }, { id: 2, name: 'Item 2' }],
    metadata: {
      total: 100,
      page: 1,
      timestamp: Date.now()
    },
    onComplete: (result) => {
      console.log('处理完成:', result);
    }
  }
});

element.dispatchEvent(event);

// 监听并使用数据
element.addEventListener('dataLoaded', (event) => {
  const { items, metadata, onComplete } = event.detail;

  console.log(`加载了 ${items.length} 条数据，共 ${metadata.total} 条`);

  // 处理数据
  items.forEach(item => {
    processItem(item);
  });

  // 调用回调
  onComplete({ success: true });
});
```

**规则 3: 设置 bubbles 实现事件冒泡**

设置 `bubbles: true` 使自定义事件可以冒泡，允许父元素或 `document` 监听事件。这对实现事件总线和组件解耦很有用。

```javascript
// 在子元素上派发事件
const button = document.querySelector('.child-button');

const event = new CustomEvent('action', {
  detail: { type: 'save' },
  bubbles: true // 允许冒泡
});

button.dispatchEvent(event);

// 在父元素上监听
const parent = document.querySelector('.parent');
parent.addEventListener('action', (event) => {
  console.log('父元素监听到:', event.detail);
});

// 在 document 上监听（事件总线模式）
document.addEventListener('action', (event) => {
  console.log('document 监听到:', event.detail);
  console.log('事件来源:', event.target); // button 元素
});

// ❌ bubbles: false（默认值）
const noBubbleEvent = new CustomEvent('noAction', {
  bubbles: false // 不冒泡
});

button.dispatchEvent(noBubbleEvent);
// parent 和 document 无法监听到此事件
```

**规则 4: 使用 cancelable 允许取消事件**

设置 `cancelable: true` 允许监听器调用 `preventDefault()` 取消事件。`dispatchEvent()` 返回布尔值指示事件是否被取消。

```javascript
class Form {
  submit() {
    // 派发可取消的事件
    const event = new CustomEvent('beforeSubmit', {
      detail: { formData: this.getData() },
      cancelable: true // 允许取消
    });

    const allowed = this.element.dispatchEvent(event);

    if (!allowed) {
      console.log('提交被取消');
      return false;
    }

    // 继续提交
    this.doSubmit();
    return true;
  }
}

// 监听并可能取消事件
form.element.addEventListener('beforeSubmit', (event) => {
  const { formData } = event.detail;

  // 验证表单
  if (!validateForm(formData)) {
    event.preventDefault(); // 取消提交
    alert('表单验证失败');
  }
});

// dispatchEvent 返回值
const event = new CustomEvent('test', { cancelable: true });
const result = element.dispatchEvent(event);
// result === true: 事件未被取消
// result === false: 事件被 preventDefault() 取消
```

**规则 5: 使用事件总线实现组件解耦**

创建一个事件总线（EventBus）作为中央事件分发器，所有组件通过事件总线通信，而不是直接调用彼此的方法。

```javascript
// 事件总线实现
class EventBus {
  constructor() {
    this.bus = document.createElement('div');
  }

  emit(eventName, data) {
    const event = new CustomEvent(eventName, { detail: data });
    this.bus.dispatchEvent(event);
  }

  on(eventName, callback) {
    this.bus.addEventListener(eventName, (event) => {
      callback(event.detail);
    });
  }

  off(eventName, callback) {
    this.bus.removeEventListener(eventName, callback);
  }
}

const bus = new EventBus();

// 组件 A：派发事件
class FilterPanel {
  updateFilter(filters) {
    bus.emit('filterChanged', { filters });
  }
}

// 组件 B：监听事件
class Chart {
  constructor() {
    bus.on('filterChanged', (data) => {
      this.refresh(data.filters);
    });
  }

  refresh(filters) {
    console.log('图表更新:', filters);
  }
}

// 组件 C：监听事件
class DataTable {
  constructor() {
    bus.on('filterChanged', (data) => {
      this.refresh(data.filters);
    });
  }

  refresh(filters) {
    console.log('表格更新:', filters);
  }
}

// 组件完全解耦，彼此不需要知道对方的存在
```

**规则 6: 自定义事件常见应用场景**

自定义事件适用于组件通信、状态同步、流程控制等场景，是实现松耦合架构的关键技术。

```javascript
// 1. 组件生命周期通知
class Component {
  mount() {
    // 挂载完成后通知
    this.emit('mounted', { component: this });
  }

  emit(eventName, data) {
    const event = new CustomEvent(eventName, { detail: data, bubbles: true });
    this.element.dispatchEvent(event);
  }
}

// 2. 异步操作完成通知
class DataLoader {
  async load() {
    const data = await fetch('/api/data').then(r => r.json());

    document.dispatchEvent(new CustomEvent('dataLoaded', {
      detail: { data, timestamp: Date.now() }
    }));
  }
}

// 3. 用户交互流程控制
class Wizard {
  nextStep() {
    const event = new CustomEvent('beforeStepChange', {
      detail: { from: this.currentStep, to: this.currentStep + 1 },
      cancelable: true
    });

    if (!this.element.dispatchEvent(event)) {
      return; // 步骤切换被取消
    }

    this.currentStep++;
  }
}

// 4. 状态变化广播
class Store {
  setState(newState) {
    this.state = { ...this.state, ...newState };

    document.dispatchEvent(new CustomEvent('stateChanged', {
      detail: { state: this.state }
    }));
  }
}

// 5. 跨窗口通信（配合 postMessage）
window.addEventListener('message', (event) => {
  if (event.origin === 'https://trusted.com') {
    document.dispatchEvent(new CustomEvent('externalMessage', {
      detail: event.data
    }));
  }
});
```

---

**记录者注**:

浏览器提供了丰富的原生事件（click、submit、keydown 等），但它们仅涵盖用户交互和文档状态变化。当我们需要表达业务逻辑中的自定义状态和流程时，原生事件就不够用了。这时，自定义事件成为了扩展浏览器事件系统的关键工具。

自定义事件的核心价值在于解耦。组件通过派发事件表达"发生了什么"，而不是直接调用其他组件的方法。监听器订阅感兴趣的事件，彼此之间互不依赖。这种发布-订阅模式让代码更灵活、可维护、易扩展。

记住：**使用 `CustomEvent` 创建事件，通过 `detail` 传递数据，设置 `bubbles` 实现冒泡，设置 `cancelable` 允许取消。自定义事件是构建松耦合架构的基石**。
