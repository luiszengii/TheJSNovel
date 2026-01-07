《第52次记录: 类继承战争 —— 重构之路的抉择》

---

## 重构讨论

周一上午九点, 你打开项目看板, 看到新建的任务:"重构用户权限系统 - 优先级: 中 - 预计时间: 1周"。

这是个计划已久的重构任务。现有的用户权限系统是两年前用传统构造函数写的, 代码能用, 但维护起来很吃力。随着团队新人加入, 大家都更习惯ES6的class语法, 你们决定趁着这次功能升级的机会, 把整个继承体系现代化。

你端着咖啡, 翻开旧代码。权限系统有三层继承: 基础User类、管理员Admin类、超级管理员SuperAdmin类。代码是这样的:

```javascript
function User(name, email) {
    this. name = name;
    this. email = email;
    this. permissions = ['read'];
}

User. prototype. hasPermission = function(perm) {
    return this. permissions. includes(perm);
};

function Admin(name, email, department) {
    User. call(this, name, email);
    this. department = department;
    this. permissions. push('write', 'delete');
}

Admin. prototype = Object. create(User. prototype);
Admin. prototype. constructor = Admin;
```

"典型的ES5继承模式。"你在笔记本上写下评价,"可读性差, 容易出错, 三步骤缺一不可。"

同事老李走过来:"开始重构了? 我看了一下旧代码, 继承链还挺复杂的。"

"是啊,"你说,"我在想要不要全部改成class, 但又担心有什么坑。毕竟这是核心权限系统, 不能出问题。"

老李坐下来:"有时间慢慢改, 不用急。我之前重构过类似的, class确实清晰很多, 但有些细节要注意。"

你们俩开始讨论重构方案。窗外阳光正好, 办公室里很安静, 这种不赶时间的技术讨论, 让你觉得很放松。

---

## 方案对比

周一下午, 你开始尝试用class重写User类。第一版很顺利:

```javascript
class User {
    constructor(name, email) {
        this. name = name;
        this. email = email;
        this. permissions = ['read'];
    }

    hasPermission(perm) {
        return this. permissions. includes(perm);
    }
}
```

"简洁多了!"你看着新代码, 很满意。然后开始写Admin类:

```javascript
class Admin extends User {
    constructor(name, email, department) {
        super(name, email);
        this. department = department;
        this. permissions. push('write', 'delete');
    }

    manageUsers() {
        console. log(`${this. name} managing ${this. department}`);
    }
}
```

你创建实例测试:

```javascript
const admin = new Admin('Alice', 'alice@example. com', 'IT');
console. log(admin. permissions); // ['read', 'write', 'delete']
admin. manageUsers(); // 'Alice managing IT'
console. log(admin. hasPermission('write')); // true
```

"完美!"你正想提交代码, 突然想起一个问题:"等等, permissions数组是在父类构造函数里创建的, 每个实例都应该有独立的数组吧?"

你写了个测试:

```javascript
const user1 = new User('Bob', 'bob@example. com');
const user2 = new User('Charlie', 'charlie@example. com');

user1. permissions. push('admin');
console. log(user2. permissions); // ['read'] - 独立的, 没问题
```

"看起来没问题。"你松了口气。

周二上午, 你继续重构SuperAdmin类。这个类需要覆盖父类的一些方法, 还要调用父类的方法:

```javascript
class SuperAdmin extends Admin {
    constructor(name, email, department) {
        super(name, email, department);
        this. permissions. push('superuser');
    }

    manageUsers() {
        super. manageUsers(); // 调用父类方法
        console. log('With superuser privileges');
    }

    resetPermissions() {
        this. permissions = ['read', 'write', 'delete', 'superuser'];
    }
}
```

你测试了一下, 功能正常。但老李走过来看了看代码, 皱起眉头:"这里有个隐患。"

"什么隐患?"你问。

"你看, permissions数组是在构造函数里初始化的, 每次继承都要重新push。如果继承层级更深, 每一层都要记得处理permissions, 容易遗漏。"

老李说得对。你想了想:"那能不能用static或者别的方式, 让每个类有默认的permissions配置?"

老李打开另一个编辑器:"我之前用过一个模式, 在类上定义静态属性, 然后在构造函数里合并:"

```javascript
class User {
    static DEFAULT_PERMISSIONS = ['read'];

    constructor(name, email) {
        this. name = name;
        this. email = email;
        this. permissions = [... this. constructor. DEFAULT_PERMISSIONS];
    }
}

class Admin extends User {
    static DEFAULT_PERMISSIONS = ['read', 'write', 'delete'];
}

class SuperAdmin extends Admin {
    static DEFAULT_PERMISSIONS = ['read', 'write', 'delete', 'superuser'];
}
```

"这样每个类的权限配置一目了然, 而且不用在构造函数里层层push。"老李解释。

你眼前一亮:"这样确实更清晰! 而且如果以后要新增一个角色, 只要定义好DEFAULT_PERMISSIONS就行了。"

周三, 你继续优化, 发现了class的另一个好处——私有字段:

```javascript
class User {
    #internalId; // 私有字段

    constructor(name, email) {
        this. name = name;
        this. email = email;
        this.#internalId = Math. random(). toString(36). substr(2, 9);
    }

    getInternalId() {
        return this.#internalId;
    }
}

const user = new User('David', 'david@example. com');
console. log(user. getInternalId()); // 可以访问
console. log(user.#internalId);     // 语法错误! 真正的私有
```

"传统构造函数做不到这个。"你记录在笔记里,"class的私有字段是真正的私有, 外部完全访问不了。"

周四, 重构基本完成, 你开始对比新旧代码。你发现, 虽然功能一样, 但class版本的可读性和可维护性都远远超过旧版本。

---

## Code Review

周五上午, 你和老李一起做Code Review, 对比了两种继承方式的优缺点。

**传统构造函数继承 (ES5)**

```javascript
// 父类
function User(name, email) {
    this. name = name;
    this. email = email;
    this. permissions = ['read'];
}

User. prototype. hasPermission = function(perm) {
    return this. permissions. includes(perm);
};

// 子类 - 需要三步骤
function Admin(name, email, department) {
    // 步骤1: 借用构造函数
    User. call(this, name, email);
    this. department = department;
    this. permissions. push('write');
}

// 步骤2: 设置原型链
Admin. prototype = Object. create(User. prototype);

// 步骤3: 修复constructor
Admin. prototype. constructor = Admin;

// 添加方法
Admin. prototype. manageUsers = function() {
    console. log('Managing users');
};
```

**ES6 Class继承**

```javascript
// 父类
class User {
    static DEFAULT_PERMISSIONS = ['read'];

    constructor(name, email) {
        this. name = name;
        this. email = email;
        this. permissions = [... this. constructor. DEFAULT_PERMISSIONS];
    }

    hasPermission(perm) {
        return this. permissions. includes(perm);
    }
}

// 子类 - 简洁清晰
class Admin extends User {
    static DEFAULT_PERMISSIONS = ['read', 'write', 'delete'];

    constructor(name, email, department) {
        super(name, email); // 调用父类构造函数
        this. department = department;
    }

    manageUsers() {
        console. log('Managing users');
    }
}
```

老李总结:"class版本的优势很明显: 语法清晰、extends一行搞定原型链、super关键字方便、支持私有字段。"

"缺点呢?"你问。

"主要是兼容性, 老版本浏览器不支持。但我们项目都是现代浏览器, 没问题。"老李说,"还有就是class本质上还是原型继承, 只是语法糖, 理解原型链还是很重要的。"

你们还对比了方法覆盖的写法:

**调用父类方法**

```javascript
// ES5: 麻烦
Admin. prototype. manageUsers = function() {
    User. prototype. hasPermission. call(this, 'admin');
    console. log('Managing');
};

// ES6: 简洁
class Admin extends User {
    manageUsers() {
        super. hasPermission('admin'); // super关键字
        console. log('Managing');
    }
}
```

周五下午, 你完成了所有重构, 并写了完整的单元测试。新的class继承体系清晰易懂, 代码量减少了30%, 可读性大大提升。

你提交了Pull Request, 标题写着:"重构权限系统为ES6 class - 提升可维护性"。

老李review后评论:"改得不错, 以后新人看这代码也能快速理解了。"

---

## 最佳实践

**规则 1: ES5继承的三步骤**

传统构造函数继承必须完成三个步骤, 缺一不可:

```javascript
function Child(value) {
    Parent. call(this, value); // 1. 借用构造函数
}
Child. prototype = Object. create(Parent. prototype); // 2. 原型链
Child. prototype. constructor = Child; // 3. 修复constructor
```

容易出错, 维护困难。

---

**规则 2: ES6 class继承**

```javascript
class Child extends Parent {
    constructor(value) {
        super(value); // 调用父类构造函数
        this. childProp = 'child';
    }

    childMethod() {
        super. parentMethod(); // 调用父类方法
        // 子类逻辑
    }
}
```

语法清晰, extends和super让继承变得简单。

---

**规则 3: super关键字**

```javascript
class Admin extends User {
    constructor(name, email, dept) {
        // super()必须在访问this之前调用
        super(name, email); // 调用父类构造函数
        this. dept = dept; // 现在可以用this了
    }

    manageUsers() {
        super. hasPermission('admin'); // 调用父类方法
        console. log('Managing');
    }
}
```

super()调用父类构造函数, super. method()调用父类方法。

---

**规则 4: 静态方法和属性**

```javascript
class User {
    // 静态属性
    static DEFAULT_ROLE = 'guest';

    // 静态方法
    static createGuest() {
        return new User('Guest', 'guest@example. com');
    }

    constructor(name, email) {
        this. name = name;
    }
}

// 调用静态方法
const guest = User. createGuest();

// 继承静态成员
class Admin extends User {
    static DEFAULT_ROLE = 'admin'; // 覆盖父类静态属性
}

console. log(Admin. DEFAULT_ROLE); // 'admin'
```

---

**规则 5: 私有字段 (#)**

```javascript
class User {
    #password; // 私有字段

    constructor(name, password) {
        this. name = name; // 公开
        this.#password = password; // 私有
    }

    checkPassword(input) {
        return this.#password === input; // 内部可访问
    }
}

const user = new User('Alice', 'secret123');
console. log(user. name); // 'Alice'
console. log(user.#password); // SyntaxError!
```

私有字段只能在类内部访问, 真正的封装。

---

**规则 6: class是语法糖, 本质是原型**

```javascript
class User {
    constructor(name) {
        this. name = name;
    }
    greet() {
        console. log('Hi, ' + this. name);
    }
}

// 等价于:
function User(name) {
    this. name = name;
}
User. prototype. greet = function() {
    console. log('Hi, ' + this. name);
};

// class本质上还是函数
typeof User; // 'function'

// 方法在原型上
User. prototype. greet; // function
```

理解原型链依然重要, class只是更好的语法。

---

**事故档案编号**: OBJ-2024-1752
**影响范围**: 代码重构, 继承体系设计
**根本原因**: 传统构造函数继承复杂易错, ES6 class提供更好的语法
**修复成本**: 中等(重构需要时间, 但提升长期可维护性)

这是JavaScript世界第52次被记录的继承体系重构。ES5的构造函数继承需要三步骤, 容易出错且可读性差。ES6的class提供了extends、super、静态成员、私有字段等现代特性, 让继承变得简单清晰。虽然class本质上仍是原型继承的语法糖, 但它极大提升了代码可读性和可维护性。在现代项目中, class是继承的首选方案。

---
