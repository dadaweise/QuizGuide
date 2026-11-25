"""Practice-mode hint ladders, one per problem.

make.py replaces <!--ladder:key--> in index.src.html with a task line and a ladder:
hints in order, then an "Answer" step (reveals the problem's hidden content), then a "New case" step.
Texts are HTML. Every key here must be placed in the page, and every placeholder must have a key.
"""

H = {}


def ladder(key, task, hints, new_case, link, link_text, title=None):
    H[key] = {"task": task, "hints": hints, "new_case": new_case, "link": link, "link_text": link_text, "title": title}


# ------------------------------------------------------------------ Part 1: server bugs

ladder(
    "s1",
    "The server does not compile. Find the <em>first</em> cause in the error list and fix it.",
    [
        ("Where to look", "Run <code>cargo check</code> and read only the first few errors. They are <code>E0432 unresolved import</code>, and they all point into one folder path."),
        ("What to compare", "Open the folder <code>core/domain/entity/</code> next to its <code>mod.rs</code>. Count the <code>.rs</code> files, then count the <code>pub mod</code> lines."),
        ("The cause", "A Rust file only becomes part of the program when its parent declares it with <code>pub mod name;</code>. Which file names are in the folder but have no line in <code>mod.rs</code>?", ["s1"]),
    ],
    "Whenever an error says <em>could not find X in Y</em>, compare the files in folder <code>Y</code> with the <code>pub mod</code> lines in <code>Y/mod.rs</code> (or <code>Y.rs</code>). Fix this kind of error first: it causes dozens of others.",
    "#pb-import", "New case · Import",
    title='S1 · Import'
)

ladder(
    "s2",
    "After S1, the errors move to the service trait. Make it compile, and make it match what the HTTP handlers call.",
    [
        ("Where to look", "<code>port/inbound/service_trait.rs</code>. Read its first lines: what does it <code>use</code>?"),
        ("What to compare", "For each type the trait mentions (<code>OrderItemResponse</code>, <code>EventLogModel</code>, <code>WarehouseModelEx</code> …), find where it is defined in <code>dto/</code> or <code>entity/</code>. <code>repository_trait.rs</code> shows the alias style to copy."),
        ("The second problem", "Once the imports are in, compare every <code>service.xxx(</code> call in <code>server.rs</code> with the method list in the trait. One method is called by a handler and written in <code>service.rs</code>, but the trait never declares it.", ["s2"]),
    ],
    "A handler with <code>S: ServiceTrait</code> only sees the trait's methods. Line up three lists: the trait, the <code>impl</code>, and every call site. A name that is missing from any one of them is the bug.",
    "#pb-trait", "New case · Trait",
    title='S2 · Import + Trait'
)

ladder(
    "s3",
    "<code>service.rs</code> still fails with <em>cannot find trait</em> and <em>cannot find type</em>. Fix it.",
    [
        ("Where to look", "The top of <code>core/service/service.rs</code>. Which two things does it import?"),
        ("What to collect", "List every name the file uses but doesn't define: the two traits, the response DTOs (<code>Location</code>, <code>OrderItemResponse</code> …), the ActiveModels and the Models."),
        ("How to write it", "Use the alias names exactly as the body spells them (<code>OperatorActiveModel</code>, <code>OrderItemModelEx</code> …). In VS Code, <kbd>Ctrl</kbd>+<kbd>.</kbd> on a red name offers the import; then rename it to the alias.", ["s3"]),
    ],
    "In a hexagonal project each layer file imports its port traits and the domain types. When a whole file is red, copy the import block style from a sibling file that compiles (here <code>repository.rs</code>).",
    "#pb-import", "New case · Import",
    title='S3 · Import'
)

ladder(
    "s4",
    "Next comes <code>E0596 cannot borrow as mutable</code>. Fix every place, not only the first one the compiler reports.",
    [
        ("Where to look", "The error points at a <code>.push(</code> in <code>service.rs</code>. Look at the line where that vector is created."),
        ("The cause", "Rust bindings are immutable by default, and <code>push</code> needs <code>&amp;mut self</code>. What keyword is missing on that <code>let</code>?", ["s4"]),
        ("Find them all", "Search the file for <code>= Vec::new();</code>. How many of those vectors get <code>.push(…)</code> later but are not <code>let mut</code>?"),
    ],
    "Ownership bugs in a new case are usually one of: a missing <code>mut</code>, using a value after it moved (<code>E0382</code>), or two borrows that overlap. Search for the pattern once you know one instance.",
    "#pb-borrow", "New case · Ownership Borrowing",
    title='S4 · Ownership Borrowing'
)

ladder(
    "s5",
    "<code>server.rs</code> gives <code>E0308 expected associated type, found Result</code>. Fix it.",
    [
        ("Where to look", "The handlers in <code>adapter/inbound/server.rs</code>. Compare the first two dispatcher handlers with all the others, line by line."),
        ("What the service returns", "Every service method returns <code>impl Future&lt;Output = Result&lt;…&gt;&gt;</code>, not a <code>Result</code>. What turns a future into its result inside an <code>async fn</code>?", ["s5"]),
        ("Find them all", "Search the file for <code>service.</code> calls and check that each one ends with that keyword. How many lack it?"),
    ],
    "Every call to an <code>async fn</code> or an <code>impl Future</code> needs <code>.await</code>. The setter likes to remove it from the first handlers in a router group.",
    "#pb-async", "New case · Async/Await",
    title='S5 · Async/Await'
)

ladder(
    "s6",
    "The server now compiles. One ActiveModel bug is left that the compiler can't see: after a dispatch, something about the courier is wrong.",
    [
        ("Where to look", "Search <code>service.rs</code> for <code>OperatorActiveModel {</code>. Two use cases change an operator: which ones?"),
        ("What to compare", "What does <code>complete_task</code> set on the operator, and what does its comment (<code>1 itu Available</code>) say? A dispatch is the opposite action."),
        ("The cause", "In <code>dispatch_operator</code> the operator ActiveModel has only <code>id: Unchanged(…)</code>. A field left at <code>..Default::default()</code> is <em>not</em> written, so SeaORM updates nothing. Which field should dispatch set, and to what value?", ["s6"]),
    ],
    "For every state-changing use case, write down the fields that must change, then check that each one is <code>Set(…)</code>. Paired actions (assign ↔ finish, open ↔ close) flip the same field both ways.",
    "#pb-activemodel", "New case · ActiveModel",
    title='S6 <span class="tag read">Found by reading</span> · ActiveModel'
)

# ------------------------------------------------------------------ Part 2: frontend bugs

ladder(
    "f1",
    "Type-check the desktop React app (<code>npx tsc --noEmit</code> in <code>app/desktop</code>) and fix the root cause of the errors.",
    [
        ("What you see", "Five errors in four files (<code>TS2367</code>, <code>TS2345</code>), all about comparing or passing an <code>id</code>."),
        ("Don't patch each line", "Press <kbd>F12</kbd> on <code>id</code> to open the type that declares it."),
        ("What to compare", "Compare that type with the Rust struct the data comes from (<code>src-tauri/src/model/operator.rs</code>) and with <code>courier_id</code> in <code>order-item.ts</code>. What type is the id there?", ["f1"]),
    ],
    "When many TypeScript errors share one field, fix the type definition so it matches the Rust struct, not the call sites. Check names (snake_case) and types field by field.",
    "#pb-react", "New case · React",
    title='F1 <span class="tag ok">Compiler-checked</span> · React'
)

ladder(
    "t1",
    "The Tauri crate compiles, but the grading sheet says it has a bug. Find it.",
    [
        ("Where to look", "<code>src-tauri/src/controller/</code>: every <code>#[tauri::command]</code> that takes an id."),
        ("What to compare", "What do <code>get_task_list</code>, <code>complete_task</code> and <code>get_job_stats</code> do <em>before</em> they call <code>state.api_client</code>?"),
        ("The odd ones out", "Which commands skip that step? Look at the line right after their opening brace: it's blank, and in one of them it still holds four spaces.", ["t1"]),
    ],
    "When a crate compiles but has a bug, line up sibling functions (guard, call, refresh, error text). The one that differs is the bug, and a blank line is often where code was deleted.",
    "#pb-tauri", "New case · Rust tauri",
    title='T1 <span class="tag read">Found by reading</span> · Rust tauri'
)

ladder(
    "f2",
    "Compare what the Courier page shows with what the server checks when an item is delivered.",
    [
        ("Where to look", "<code>desktop/src/pages/CourierPage.tsx</code>, the two <code>&lt;Waypoint … range={distance(…)}&gt;</code> calls. It's also the newest file in the zip."),
        ("What to compare", "Write down each <code>distance(from, to)</code>: from where to where? The pickup one starts at the courier. Where does the destination one start?"),
        ("The rule it should match", "<code>complete_task</code> on the server answers 409 unless the <em>courier</em> is within 20 units of the warehouse. So which point should the destination distance be measured from?", ["f2"]),
    ],
    "Check every number the UI shows against the rule the server enforces with it. A value measured from the wrong point looks fine until you test it.",
    "#pb-frontend", "New case · frontend bug lines",
    title='Extra <span class="tag read">Found by reading</span> · Courier page'
)

# ------------------------------------------------------------------ Part 2b: full audit

ladder(
    "audit",
    "Look past the seven graded bugs. What else is wrong or risky in the code, and which of it is worth your time?",
    [
        ("Run the tools again", "After the compile fixes, run <code>cargo clippy</code> on the server and the Tauri crate, and <code>npx tsc --noEmit</code> on React. Does anything besides style hints remain?"),
        ("Use the zip's dates", "In PowerShell: <code>tar -tvf app.zip | Sort-Object { ($_ -split '\\s+')[7] } | Select-Object -Last 10</code>. Which files were saved later than the rest? Read those first, and look for blocks of empty lines."),
        ("Check every two-table write", "Find each use case that changes two tables. Are both writes inside one <code>begin()</code>/<code>commit()</code>? Look closely at <code>complete_task</code>.", ["audit"]),
        ("Decide", "For each finding choose: fix, mention, or leave. A section marked \"no bug, don't change\" means leave it."),
    ],
    "Plan 10 minutes for this pass after the graded tasks: dates in the zip, a two-table-write check, then decide fix, mention or leave.",
    "#checklist", "Checklist for the next quiz",
)

# ------------------------------------------------------------------ Part 3: optimization

ladder(
    "n1",
    "Solve the N+1 query problem for warehouse items.",
    [
        ("Where to look", "In <code>service.rs</code>, find a repository call with <code>.await</code> <em>inside</em> a <code>for</code> loop. Which endpoint uses that function?", ["n1_spot"]),
        ("Count the queries", "One query for the warehouses, then one per warehouse (55 in the seed). Did <code>cargo check</code> warn about a repository method that is never used and loads <em>all</em> inventory?"),
        ("Choose a fix", "Three ways: load everything once and group it by <code>warehouse_id</code> in a <code>HashMap</code>; eager-load it with <code>.with(…)</code> through an entity relation; or run one <code>is_in(ids)</code> query. Which files would each one change, and which sections say \"don't change\"?", ["n1_hashmap", "n1_eager"]),
    ],
    "Search every service for <code>for … { … repository … .await }</code>. Move the query before the loop (load all, <code>is_in</code>, or eager <code>.with</code>), then look up each row's children in memory.",
    "#pb-opt", "New case · optimization",
)

ladder(
    "opt",
    "Find wasted work that isn't a loop (the \"Logic optimization\" half of the line).",
    [
        ("Where to look", "<code>repository.rs</code>, saved later than most files. How does <code>get_order_item</code> find a single item?"),
        ("What to compare", "It loads <em>every</em> order item with four relations, then searches in Rust. How does <code>get_operator_by_id</code> in the same file find one row?"),
        ("The fix shape", "Put the id in the query: <code>.filter(Id.eq(…))</code> and <code>.one(…)</code>. Keep the same <code>.with(…)</code> relations and the same <code>RecordNotFound</code> error so the service doesn't change.", ["opt"]),
    ],
    "\"Load everything, then filter or search in Rust\" becomes a <code>WHERE</code> in the query. Look for <code>.all()</code> followed by a loop, <code>find</code> or <code>filter</code>.",
    "#pb-opt", "New case · optimization",
)

# ------------------------------------------------------------------ Part 4: activity log

ladder(
    "activity",
    "Continue and finish the activity log feature.",
    [
        ("Find what exists", "Search for <code>activity_log</code> in the SQL, the entity, the repository, the service, <code>server.rs</code> and the dashboard. Which side is there, reading or writing?"),
        ("Find a sibling to copy", "Another log in the project is complete. Follow it from the table to where it is called: repository → service → caller."),
        ("Plan the layers", "Repository trait + impl: insert taking an <em>ActiveModel</em>. Service trait + impl: <code>record_activity(description)</code>. In <code>service.rs</code>, where was a block of code cut out? That's where it goes.", ["log_layers"]),
        ("When to call it", "Which use cases change a courier or an item? Call it at the end of each one, after the update succeeded. What should the text say: who, what, which item?", ["log_call"]),
    ],
    "Finish a log feature in four steps: find the half that exists, copy the complete sibling log through repository → service → callers, then call it after every successful state change.",
    "#pb-log", "New case · log feature",
)

# ------------------------------------------------------------------ Part 5: sorting

ladder(
    "sort",
    "Sort the courier list by distance and specialty.",
    [
        ("Where to look", "Where is the courier list drawn (<code>couriers.map</code>)? Which helper already computes a courier's distance to the selected item's pickup?"),
        ("Decide the order first", "Who should be at the top: couriers you can't pick, or the ones you can? After that, nearest first. Where does specialty come in, and what goes last?"),
        ("Front end or back end", "In React: copy the array (<code>[...couriers]</code>) and use one comparator with tie-breakers. On the server: a new endpoint can compare the courier's specialty region id with the destination warehouse's region id. React doesn't have those ids, only names.", ["sort_react", "sort_server"]),
    ],
    "Write the sort keys in order before coding (eligible first, then the main key, then tie-breakers). Copy before sorting a prop. Do it on the server only when the rule needs data the client doesn't have.",
    "#pb-sort", "New case · sort feature",
)

# ------------------------------------------------------------------ Part 6: diagrams

ladder(
    "uc",
    "Draw the use case diagram from the code.",
    [
        ("Actors", "Which roles does the <code>role</code> table seed, and which pages does the sidebar show? The parts of <a href=\"#uc-l1\">6.1</a> follow the grading sheet line by line."),
        ("Use cases", "List the buttons that change data and the panels on each page. For each panel ask: would the user open it for its own sake, or does it only feed a button? Name each use case as the user's goal (<em>Dispatch Operator</em>), not as an HTTP call."),
        ("System and subsystems", "The rubric asks for the system, its <em>subsystems</em> and the actors. Group the use cases by router group, plus the read-only screens. Is the background event generator a person with a goal?"),
    ],
    "Roles become actors, routes and buttons become use cases, router groups become subsystems. Check that the system box and subsystem boxes are named, because the rubric scores them.",
    "#pb-diagrams", "New case · diagrams",
)

ladder(
    "dcd",
    "Draw the first cut class diagram for the whole system.",
    [
        ("Classes", "Every business table (SeaORM entity) becomes a domain class: the diagram is for the whole system, so none is optional. Then add a <code>«controller»</code> for <em>every</em> use case in your use case diagram. Related read-only use cases of one subsystem may share one controller."),
        ("Attributes", "Columns become <code>-name: type</code>, with <code>{key}</code> on ids. Foreign-key columns become arrows instead. Line 2 of <a href=\"#dcd-l2\">6.4</a> shows the code to look for."),
        ("Methods", "A domain method exists only if some use case realization sends that message. Each check or change a service function makes on one object becomes a method of that object's class, and the controller gets one method per service function. Read-only use cases add no domain methods. Put a method on the object that owns the data."),
        ("Arrows", "Navigation arrows point superior → subordinate, independent → dependent, or toward the object whose information is needed. Controllers sit at the top and point to the domain classes they use."),
    ],
    "Entities give you all the classes and attributes, the service functions give you the controllers (one per write use case, one per group of read use cases), and every <code>if</code> or change on one object in a write use case gives that object a method. Realize each write use case first, then copy its messages into the classes.",
    "#pb-diagrams", "New case · diagrams",
)

ladder(
    "act",
    "Draw the activity diagrams for Dispatch Operator and Pick Up Item.",
    [
        ("Sources", "For each use case, open the page's click handler (<code>assign()</code>, <code>act()</code>) and the service function. How many swimlanes does the book give an activity diagram for one use case? Look at Fig. 5-4 and 5-5. The parts of <a href=\"#act-l1\">6.2</a> follow the grading sheet line by line."),
        ("Where it starts", "Start at the actor's first action, the one that triggers the use case. State that must already hold (page open, item already ASSIGNED, list on screen) is a <em>precondition</em>: the book puts it in the use case description, not in the diagram (Fig. 5-2, 5-3)."),
        ("Decisions and actions", "Every <code>return Err(StatusCode::…)</code> is a decision with a <code>[guard]</code>. Every repository write is an action. Keep the order of the code."),
        ("End it properly", "Merge the error branches into one \"Show error\" action, then merge success and error into a single end node. Draw <em>both</em> use cases: the sheet averages the two."),
    ],
    "Read the service function top to bottom: each <code>if … return Err</code> is a decision with its status code as the guard, and each write is an action. Use one start, one end, and two lanes: the actor and the system.",
    "#pb-diagrams", "New case · diagrams",
)

ladder(
    "seq",
    "Draw the multilayer sequence diagrams for Dispatch Operator and Pick Up Item.",
    [
        ("Layers", "Left to right: actor, <code>«view»</code> page, <code>«boundary»</code> Tauri command and API handler, <code>«controller»</code> use case handler, domain objects, <code>«dataAccess»</code> repository. The parts of <a href=\"#seq-l1\">6.3</a> follow the grading sheet line by line."),
        ("Creation", "Who creates the domain objects? The repository reads a row and returns a model, so it creates <code>aOp</code> and <code>anItem</code>. Start each box at its creation arrow."),
        ("Checks and fragments", "Each <code>if … return Err</code> is one dashed return with a condition: <code>[not ready] Err(400)</code> (Satzinger PDF 172). Add a note that such a return ends the method. Keep one <code>alt [Ok(())] / [Err(status)]</code> frame for the reply. Each message to a domain object must be a method in your class diagram."),
        ("Order", "Follow the code's order exactly. In <code>pickup_medicine</code> the item checks come <em>before</em> the operator is loaded. Put each conditioned return right after the message that fetched the data it tests, so the order of the arrows is the order of the code. Did you start at the Tauri command's own check?"),
    ],
    "Turn each layer of the code into a lifeline, each repository read into a creation, each <code>if … return Err</code> into a conditioned return, and each check on an object into a message. Then check every message against the class diagram.",
    "#pb-diagrams", "New case · diagrams",
)
