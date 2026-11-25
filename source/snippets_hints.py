"""Syntax examples shown inside the practice-mode hints.

They come from an imagined Library case (Member, Book, Loan, Branch, BranchBook, loan_log),
so they show the syntax without giving away the Rhodev answers. Each one is the smallest
piece of code that uses every construct the matching task needs.

X[key] = (language, code). hints.py attaches keys to a hint as its third element.
The Rust examples were compiled with cargo check inside a copy of the fixed quiz server
(same SeaORM 2.0 / Axum 0.8 versions) and the TypeScript examples with tsc; see the guide footer.
"""

X = {}

# ------------------------------------------------------------------ bugs

X["s1"] = ("rust", r"""// Library: the folder core/domain/entity/ holds book.rs, member.rs, loan.rs, loan_log.rs
// entity/mod.rs needs one line per file, or that file is not part of the program
pub mod prelude;

pub mod book;
pub mod member;
pub mod loan;
pub mod loan_log;

// Only then can another file write:
// use crate::core::domain::entity::loan::{self, ActiveModel as LoanActiveModel};""")

X["s2"] = ("rust", r"""use axum::http::StatusCode;
use crate::core::domain::dto::loan::LoanResponse;                // every type the trait names
use crate::core::domain::entity::loan_log::Model as LoanLogModel;

pub trait LibraryServiceTrait: Send + Sync {
    fn view_loans(&self, member_id: i32) -> impl Future<Output = Result<Vec<LoanResponse>, StatusCode>> + Send;
    fn view_loan_log(&self) -> impl Future<Output = Result<Vec<LoanLogModel>, StatusCode>> + Send;
    // A handler calls service.lend_book(...), so the trait must declare it too:
    fn lend_book(&self, member_id: i32, book_id: i32) -> impl Future<Output = Result<(), StatusCode>> + Send;
}

// service.rs implements it with the same name, parameters and Result:
// async fn lend_book(&self, member_id: i32, book_id: i32) -> Result<(), StatusCode> { ... }""")

X["s3"] = ("rust", r"""// Top of the Library service.rs: everything the body uses but does not define
use sea_orm::{ActiveValue, DbErr};
use axum::http::StatusCode;

use crate::core::domain::dto::loan::{GetLoansRequest, LoanResponse};
use crate::core::domain::entity::{
    loan::{ActiveModel as LoanActiveModel, ModelEx as LoanModelEx},
    loan_log::{ActiveModel as LoanLogActiveModel, Model as LoanLogModel},
    member::{ActiveModel as MemberActiveModel, Model as MemberModel},
};
use crate::port::{inbound::service_trait::LibraryServiceTrait, outbound::repository_trait::LibraryRepoTrait};""")

X["s4"] = ("rust", r"""let mut titles = Vec::new();      // without `mut`: E0596 cannot borrow `titles` as mutable
for loan in loans {
    titles.push(loan.title);       // push changes the vector, so the binding must be `mut`
}

let name = member.full_name.clone();   // E0382 fix: clone (or read it) before the value moves
let response = MemberResponse { full_name: member.full_name };
println!("{name} -> {}", response.full_name);""")

X["s5"] = ("rust", r"""async fn get_loans(
    State(service): State<Arc<S>>,
    Json(payload): Json<GetLoansRequest>,
) -> impl IntoResponse {
    // Without .await this is still a Future, and `match` on Ok/Err gives E0308
    let loans = service.view_loans(payload.member_id).await;

    match loans {
        Ok(loans) => (StatusCode::OK, Json(loans)).into_response(),
        Err(status_code) => (status_code, "Error retrieving loans").into_response(),
    }
}""")

X["s6"] = ("rust", r"""// Lend a book: the member can no longer borrow, the loan becomes LENT.
// Returning the book flips the same fields back (can_borrow = 1, status = 3).
let member_active = MemberActiveModel {
    id: ActiveValue::Unchanged(member_id),   // WHERE id = member_id (not written)
    can_borrow: ActiveValue::Set(0),         // written; leave this out and nothing changes
    ..Default::default()                     // every other field is NotSet: not written
};

let loan_active = LoanActiveModel {
    id: ActiveValue::Unchanged(loan_id),
    status: ActiveValue::Set(2),
    lent_at: ActiveValue::Set(chrono::Utc::now()),
    ..Default::default()
};""")

X["f1"] = ("ts", r"""// Rust struct the data comes from (src-tauri/src/model/member.rs):
//   pub struct Member { pub id: i32, pub full_name: String, pub can_borrow: i32 }
export type Member = {
    id: number;          // i32 -> number, never string
    full_name: string;   // same snake_case name as the Rust field
    can_borrow: number;
};

export type Loan = { id: number; member_id: number | null };  // Option<i32> -> number | null

export function borrowerOf(members: Member[], loan: Loan) {
    return members.find((m) => m.id === loan.member_id) ?? null;  // number === number
}""")

X["t1"] = ("rust", r"""#[tauri::command(rename_all = "snake_case")]
pub async fn return_book(
    state: State<'_, AppState>,
    member_id: i32,
    loan_id: i32,
) -> Result<(), String> {
    if member_id <= 0 || loan_id <= 0 {                      // the guard its siblings have
        return Err("Invalid member or loan".to_string());
    }

    let result = state.api_client.return_book(member_id, loan_id).await;

    match result {
        Ok(_) => {
            state.refresh.notify_one();                      // wake the poller
            Ok(())
        }
        Err(status_code) => Err(format!("Error returning book ({})", status_code)),
    }
}""")

X["f2"] = ("tsx", r"""// Library rule on the server: a return is accepted only when the MEMBER is within
// 20 units of the branch. So the number on screen must start at the member too.
const toBranch = distance(member.x_position, member.y_position, loan.branch.x_position, loan.branch.y_position);
const toShelf = distance(member.x_position, member.y_position, loan.shelf.x_position, loan.shelf.y_position);

<Waypoint label="SHELF" location={loan.shelf} range={toShelf} />
<Waypoint label="RETURN / BRANCH" location={loan.branch} range={toBranch} />""")

X["audit"] = ("rust", r"""// Two tables change in one use case: both writes on one transaction, or neither
// (needs `use sea_orm::TransactionTrait;`)
async fn return_loan(&self, loan: LoanActiveModel, book_id: i32) -> Result<(), DbErr> {
    let tx = self.database_connection.begin().await?;

    loan.update(&tx).await?;                                  // write 1 on tx

    Book::update_many()                                       // write 2 on the same tx
        .col_expr(book::Column::Copies, Expr::col(book::Column::Copies).add(1))
        .filter(book::Column::Id.eq(book_id))
        .exec(&tx)
        .await?;

    tx.commit().await?;                                       // nothing is saved before this
    Ok(())
}""")

# ------------------------------------------------------------------ optimization

X["n1_spot"] = ("rust", r"""// The N+1 shape: 1 query for the branches, then 1 more per branch
let branches = self.repository.load_branches().await.unwrap();
for branch in branches {
    let books = self.repository.load_branch_books(branch.id).await;   // a query inside the loop
    // ...
}""")

X["n1_hashmap"] = ("rust", r"""// Option A: one query before the loop, then group the rows in memory
// (top of file: use std::collections::HashMap;)
let all_books = self.repository.load_all_branch_books().await;
if all_books.is_err() {
    return Err(StatusCode::INTERNAL_SERVER_ERROR);
}

let mut books_by_branch: HashMap<i32, Vec<BranchBookModelEx>> = HashMap::new();
for row in all_books.unwrap() {
    books_by_branch.entry(row.branch_id).or_default().push(row);
}

for branch in branches {
    let books = books_by_branch.remove(&branch.id).unwrap_or_default();   // no query here
    for row in books {
        let title = match row.book.into_option() {
            Some(book) => book.title,
            None => "Unknown book".to_string(),
        };
        // build the response item with title and row.quantity
    }
}""")

X["n1_eager"] = ("rust", r"""// Option B: eager loading through the relation (branch.rs gets
//   #[sea_orm(has_many)] pub branch_books: HasMany<super::branch_book::Entity>, )
let branches = Branch::load()
    .with((BranchBook, Book))                     // branch -> its rows -> each row's book
    .all(&self.database_connection)
    .await?;
for branch in branches {
    for row in branch.branch_books { /* row.quantity, row.book.into_option() */ }
}

// Option C: one WHERE ... IN query for exactly these branches
let ids: Vec<i32> = branches_list.iter().map(|b| b.id).collect();
let rows = BranchBook::load()
    .filter(branch_book::Column::BranchId.is_in(ids))
    .with(Book)
    .all(&self.database_connection)
    .await?;""")

X["opt"] = ("rust", r"""async fn get_loan(&self, loan_id: i32) -> Result<LoanModelEx, DbErr> {
    let loan = Loan::load()
        .filter(loan::Column::Id.eq(loan_id))   // WHERE id = ? instead of loading every loan
        .with(Book)
        .with(Member)
        .one(&self.database_connection)         // Ok(Some(row)) or Ok(None)
        .await;

    match loan {
        Ok(Some(loan)) => Ok(loan),
        Ok(None) => Err(DbErr::RecordNotFound(format!("Loan with ID {} not found", loan_id))),
        Err(err) => Err(err),
    }
}""")

# ------------------------------------------------------------------ activity log

X["log_layers"] = ("rust", r"""// 1. port/outbound/repository_trait.rs
fn insert_loan_log(&self, loan_log: LoanLogActiveModel) -> impl Future<Output = Result<(), DbErr>> + Send;

// 2. adapter/outbound/repository.rs   (needs ActiveModelTrait in the sea_orm use line)
async fn insert_loan_log(&self, loan_log: LoanLogActiveModel) -> Result<(), DbErr> {
    let result = loan_log.insert(&self.database_connection).await;

    match result {
        Ok(_) => Ok(()),
        Err(err) => Err(err),
    }
}

// 3. port/inbound/service_trait.rs
fn record_loan(&self, description: String) -> impl Future<Output = Result<(), StatusCode>> + Send;

// 4. core/service/service.rs
async fn record_loan(&self, description: String) -> Result<(), StatusCode> {
    if description.is_empty() {
        return Err(StatusCode::BAD_REQUEST);
    }

    let loan_log = LoanLogActiveModel {
        description: ActiveValue::Set(description),
        ..Default::default()                      // id and created_at come from the database
    };

    let record_result = self.repository.insert_loan_log(loan_log).await;

    match record_result {
        Ok(_) => Ok(()),
        Err(_) => Err(StatusCode::INTERNAL_SERVER_ERROR),
    }
}""")

X["log_call"] = ("rust", r"""// End of lend_book, after the write succeeded
let lend_result = self.repository.lend_book(member_active, loan_active).await;
if lend_result.is_err() {
    return Err(StatusCode::INTERNAL_SERVER_ERROR);   // failed: no log entry
}

// who, what, which item: build the text from values you still own
let description = format!("{} borrowed \"{}\" (loan #{})", member.full_name, book_title, loan_id);
self.record_loan(description).await?;               // Err(StatusCode) passes straight up

Ok(())""")

# ------------------------------------------------------------------ sorting

X["sort_react"] = ("tsx", r"""// Copy first: never sort the prop in place
const sorted = [...members].sort((a, b) =>
    b.can_borrow - a.can_borrow                                        // 1. can borrow first (1 before 0)
    || distance(a.x_position, a.y_position, branch.x_position, branch.y_position)
     - distance(b.x_position, b.y_position, branch.x_position, branch.y_position)   // 2. nearest first
    || Number(b.genre === book.genre) - Number(a.genre === book.genre) // 3. same genre first
    || a.full_name.localeCompare(b.full_name)                          // 4. tie-break by name
);

{sorted.map((m) => <li key={m.id}>{m.full_name}</li>)}""")

X["sort_server"] = ("rust", r"""// On the server (top of file: use std::cmp::Ordering;)
let dist = |m: &MemberModel| ((m.x_position - branch_x).powi(2) + (m.y_position - branch_y).powi(2)).sqrt();

members.sort_by(|a, b| {
    b.can_borrow.cmp(&a.can_borrow)                                    // 1. can borrow first
        .then(dist(a).partial_cmp(&dist(b)).unwrap_or(Ordering::Equal)) // 2. nearest (f32 needs partial_cmp)
        .then((a.genre != genre).cmp(&(b.genre != genre)))             // 3. same genre first (false < true)
        .then(a.full_name.cmp(&b.full_name))                           // 4. tie-break
});""")
