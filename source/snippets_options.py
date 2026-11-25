"""Alternative answers the reader chooses between: N+1 options B and C, and the backend sort option.

Each option was applied to a scratch copy of the project and compiled:
server with cargo check, Tauri crate with cargo check, React with npx tsc --noEmit.
"""

O = {}

# ------------------------------------------------------------------ N+1 option B: eager loading

O["n1b_entity"] = r"""// core/domain/entity/warehouse.rs: inside Model, under the existing `medicines` field
#[sea_orm(has_many, via = "warehouse_inventory")]
pub medicines: HasMany<super::medicine::Entity>,
#[sea_orm(has_many)]
pub warehouse_inventories: HasMany<super::warehouse_inventory::Entity>,   // new"""

O["n1b_repo"] = r"""// port/outbound/repository_trait.rs, next to load_warehouses
fn load_warehouses_with_inventory(&self) -> impl Future<Output = Result<Vec<WarehouseModelEx>, DbErr>> + Send;

// adapter/outbound/repository.rs
async fn load_warehouses_with_inventory(&self) -> Result<Vec<WarehouseModelEx>, DbErr> {
    // Eager loading: warehouse + region + inventory + medicine, tanpa query per warehouse
    let warehouses = Warehouse::load()
    .with(Region)
    .with((WarehouseInventory, Medicine))
    .all(&self.database_connection).await;

    match warehouses {
        Ok(warehouses) => Ok(warehouses),
        Err(err) => Err(err),
    }
}"""

O["n1b_service"] = r"""async fn view_warehouse_list(&self) -> Result<Vec<WarehouseResponse>, StatusCode> {

    // Satu pemanggilan: SeaORM mengambil inventory semua warehouse sekaligus
    let warehouses = self.repository.load_warehouses_with_inventory().await;
    if warehouses.is_err() {
        return Err(StatusCode::INTERNAL_SERVER_ERROR);
    }

    let warehouses = warehouses.unwrap();
    let mut warehouse_data = Vec::new();

    for warehouse in warehouses {
        let mut items = Vec::new();

        for item in warehouse.warehouse_inventories {
            let medicine_name = match item.medicine.into_option() {
                Some(medicine) => medicine.name,
                None => "Unnamed Medicine".to_string(),
            };

            items.push(WarehouseInventoryItem {
                medicine_id: item.medicine_id,
                medicine_name,
                quantity: item.quantity,
                reorder_threshold: Some(item.reorder_threshold),
            });
        }

        let region = match warehouse.region.into_option() {
            Some(region) => region.name,
            None => String::new(),
        };

        warehouse_data.push(WarehouseResponse {
            id: warehouse.id,
            name: warehouse.name,
            region,
            capacity: warehouse.capacity,
            x_position: warehouse.x_position,
            y_position: warehouse.y_position,
            inventory: items,
        });
    }

    Ok(warehouse_data)
}"""

O["n1b_trap"] = r"""// Looks right, but loses the stock numbers:
Warehouse::load().with(Region).with(Medicine)
// `medicines` goes THROUGH warehouse_inventory (via = "warehouse_inventory"),
// so you get the medicine rows, not quantity or reorder_threshold."""

# ------------------------------------------------------------------ N+1 option C: one batch query with IN (...)

O["n1c_repo"] = r"""// port/outbound/repository_trait.rs
fn load_inventory_for_warehouses(&self, warehouse_ids: Vec<i32>) -> impl Future<Output = Result<Vec<WarehouseInventoryModelEx>, DbErr>> + Send;

// adapter/outbound/repository.rs
async fn load_inventory_for_warehouses(&self, warehouse_ids: Vec<i32>) -> Result<Vec<WarehouseInventoryModelEx>, DbErr> {
    // Satu query: WHERE warehouse_id IN (...)
    let warehouse_inventory = WarehouseInventory::load()
    .filter(warehouse_inventory::Column::WarehouseId.is_in(warehouse_ids))
    .with(Medicine)
    .all(&self.database_connection).await;

    match warehouse_inventory {
        Ok(warehouse_inventory) => Ok(warehouse_inventory),
        Err(err) => Err(err),
    }
}"""

O["n1c_service"] = r"""// view_warehouse_list: same as option A, except how the inventory is loaded
let warehouses = warehouses.unwrap();

// Kumpulkan id semua warehouse, lalu ambil inventory-nya dalam satu query
let mut warehouse_ids = Vec::new();
for warehouse in &warehouses {
    warehouse_ids.push(warehouse.id);
}

let inventory = self.repository.load_inventory_for_warehouses(warehouse_ids).await;
if inventory.is_err() {
    return Err(StatusCode::INTERNAL_SERVER_ERROR);
}

// ... then the same HashMap grouping and warehouse loop as option A"""

# ------------------------------------------------------------------ sort option B: backend ranking

O["sortb_server"] = r"""// core/domain/dto/operator.rs
#[derive(Deserialize)]
pub struct RecommendCourierRequest {
    pub order_item_id: i32,
}

// port/inbound/service_trait.rs
fn recommend_couriers(&self, order_item_id: i32) -> impl Future<Output = Result<Vec<OperatorDetailsResponse>, StatusCode>> + Send;

// adapter/inbound/server.rs: route in dispatcher_router, and the handler
.route("/recommend-couriers", post(Self::recommend_couriers))

async fn recommend_couriers(
    State(service): State<Arc<S>>,
    Json(payload): Json<RecommendCourierRequest>
) -> impl IntoResponse {
    let result = service.recommend_couriers(payload.order_item_id).await;

    match result {
        Ok(couriers) => (StatusCode::OK, Json(couriers)).into_response(),
        Err(status_code) => (status_code, "Error recommending couriers").into_response(),
    }
}"""

O["sortb_service"] = r"""// core/service/service.rs   (top of file: use std::{cmp::Ordering, collections::HashMap};)
async fn recommend_couriers(&self, order_item_id: i32) -> Result<Vec<OperatorDetailsResponse>, StatusCode> {
    if order_item_id <= 0 {
        return Err(StatusCode::BAD_REQUEST);
    }

    let order_item = self.repository.get_order_item(order_item_id).await;
    if let Err(DbErr::RecordNotFound(_)) = order_item {
        return Err(StatusCode::NOT_FOUND);
    }
    if order_item.is_err() {
        return Err(StatusCode::INTERNAL_SERVER_ERROR);
    }

    let order_item = order_item.unwrap();

    // Titik pickup (manufacturer) untuk jarak
    let mut pickup = (0.0, 0.0);
    if let Some(medicine) = order_item.medicine.into_option() {
        if let Some(manufacturer) = medicine.manufacturer.into_option() {
            pickup = (manufacturer.x_position, manufacturer.y_position);
        }
    }

    // Region warehouse tujuan untuk specialty
    let mut destination_region = None;
    if let Some(order) = order_item.order.into_option() {
        if let Some(warehouse) = order.warehouse.into_option() {
            destination_region = Some(warehouse.region_id);
        }
    }

    let operators = self.repository.get_operator_list().await;
    if operators.is_err() {
        return Err(StatusCode::INTERNAL_SERVER_ERROR);
    }

    // Hanya courier (role 2)
    let mut couriers = Vec::new();
    for operator in operators.unwrap() {
        if operator.role_id == 2 {
            couriers.push(operator);
        }
    }

    // Available dulu, lalu specialty cocok dengan region tujuan, lalu jarak terdekat ke pickup
    couriers.sort_by(|a, b| {
        let available_a = if a.availability == 1 { 0 } else { 1 };
        let available_b = if b.availability == 1 { 0 } else { 1 };
        let match_a = if a.region_specialty_id.is_some() && a.region_specialty_id == destination_region { 0 } else { 1 };
        let match_b = if b.region_specialty_id.is_some() && b.region_specialty_id == destination_region { 0 } else { 1 };
        let distance_a = ((a.x_position - pickup.0).powi(2) + (a.y_position - pickup.1).powi(2)).sqrt();
        let distance_b = ((b.x_position - pickup.0).powi(2) + (b.y_position - pickup.1).powi(2)).sqrt();

        (available_a, match_a)
            .cmp(&(available_b, match_b))
            .then(distance_a.partial_cmp(&distance_b).unwrap_or(Ordering::Equal))
    });

    let mut courier_data = Vec::new();
    for operator in couriers {
        // same mapping to OperatorDetailsResponse as in view_operator_list
        // (race, role, place_of_birth, region_specialty from the loaded relations)
        // ...
        courier_data.push(OperatorDetailsResponse { /* ... */ });
    }

    Ok(courier_data)
}"""

O["sortb_tauri"] = r"""// src-tauri/src/model/operator.rs
#[derive(Serialize)]
pub struct RecommendCourierRequest {
    pub order_item_id: i32,
}

// src-tauri/src/model/api_client.rs (import RecommendCourierRequest at the top)
pub async fn recommend_couriers(&self, order_item_id: i32) -> Result<Vec<OperatorDetailsResponse>, StatusCode> {
    let request = RecommendCourierRequest {
        order_item_id: order_item_id,
    };

    let response = self.client
        .post(format!("{}/dispatcher/recommend-couriers", self.base_url))
        .json(&request)
        .send()
        .await;
    if response.is_err() {
        return Err(StatusCode::SERVICE_UNAVAILABLE);
    }

    let response = response.unwrap();
    if !response.status().is_success() {
        return Err(response.status());
    }

    let couriers = response.json::<Vec<OperatorDetailsResponse>>().await;

    match couriers {
        Ok(couriers) => Ok(couriers),
        Err(_) => Err(StatusCode::UNPROCESSABLE_ENTITY),
    }
}

// src-tauri/src/controller/dispatcher_controller.rs
#[tauri::command(rename_all = "snake_case")]
pub async fn get_courier_recommendation(
    state: State<'_, AppState>,
    order_item_id: i32,
) -> Result<Vec<OperatorDetailsResponse>, String> {
    if order_item_id <= 0 {
        return Err("Invalid order item".to_string());
    }

    let result = state.api_client.recommend_couriers(order_item_id).await;

    match result {
        Ok(couriers) => Ok(couriers),
        Err(status_code) => Err(format!("Error recommending couriers ({})", status_code)),
    }
}

// src-tauri/src/lib.rs, inside generate_handler![ ... ]
dispatcher_controller::get_courier_recommendation,"""

O["sortb_react"] = r"""// DispatcherPage.tsx   (import { useEffect, useState } from "react";)
// Option B: the server ranks the couriers for the selected item
const [recommended, setRecommended] = useState<number[]>([]);
const rankedItemId = item?.id ?? null;

useEffect(() => {
    if (rankedItemId === null) {
        setRecommended([]);
        return;
    }
    invoke<Operator[]>("get_courier_recommendation", { order_item_id: rankedItemId })
        .then((list) => setRecommended(list.map((c) => c.id)))
        .catch((err) => {
            setRecommended([]);
            setMessage(String(err));
        });
}, [rankedItemId]);

// Keep the live courier data from the poller, but in the server's order
function rank(c: Operator) {
    const index = recommended.indexOf(c.id);
    return index === -1 ? recommended.length : index;
}
const sortedCouriers = [...couriers].sort((a, b) => rank(a) - rank(b));

// JSX: {sortedCouriers.map((c) => { ... })}"""

# ------------------------------------------------------------------ Audit extra: delivery and stock in one transaction
# Applied to a copy of the original with only the five compile fixes, then cargo check: no errors.

O["x_atomic_before"] = r"""// service.rs, complete_task (original): two separate writes
let finish_result = self.repository.finish_order_item(operator_active, order_item_active).await;   // commit 1: DELIVERED + courier free
if finish_result.is_err() {
    return Err(StatusCode::INTERNAL_SERVER_ERROR);
}

let stock_result = self.repository.add_inventory_quantity(warehouse_id, order_item.medicine_id, order_item.quantity).await;   // write 2, outside the transaction
if stock_result.is_err() {
    return Err(StatusCode::INTERNAL_SERVER_ERROR);   // too late: the item is already DELIVERED
}"""

O["x_atomic_repo"] = r"""// port/outbound/repository_trait.rs: three more parameters
fn finish_order_item(&self, operator: OperatorActiveModel, order_item: OrderItemActiveModel, warehouse_id: i32, medicine_id: i32, quantity: i32) -> impl Future<Output = Result<(), DbErr>> + Send;

// adapter/outbound/repository.rs
async fn finish_order_item(&self, operator: OperatorActiveModel, order_item: OrderItemActiveModel, warehouse_id: i32, medicine_id: i32, quantity: i32) -> Result<(), DbErr> {

    let tx = self.database_connection.begin().await?;

    let operator_result = operator.update(&tx).await;
    if let Err(err) = operator_result {
        return Err(err);
    }

    let order_item_result = order_item.update(&tx).await;
    if let Err(err) = order_item_result {
        return Err(err);
    }

    // Same UPDATE as add_inventory_quantity, but inside this transaction
    let stock_result = WarehouseInventory::update_many()
        .col_expr(warehouse_inventory::Column::Quantity, Expr::col(warehouse_inventory::Column::Quantity).add(quantity))
        .filter(warehouse_inventory::Column::WarehouseId.eq(warehouse_id))
        .filter(warehouse_inventory::Column::MedicineId.eq(medicine_id))
        .exec(&tx)
        .await;

    match stock_result {
        Ok(result) => {
            if result.rows_affected == 0 {
                return Err(DbErr::RecordNotFound(format!("Medicine {} not found in warehouse {}", medicine_id, warehouse_id)));
            }
        }
        Err(err) => return Err(err),
    }

    tx.commit().await?;

    Ok(())
}"""

O["x_atomic_service"] = r"""// service.rs, complete_task: one call replaces the two
let finish_result = self.repository
    .finish_order_item(operator_active, order_item_active, warehouse_id, order_item.medicine_id, order_item.quantity)
    .await;
if finish_result.is_err() {
    return Err(StatusCode::INTERNAL_SERVER_ERROR);
}

Ok(())"""

# Tested in Windows PowerShell 5.1 on QUIZINITIAL/app.zip (read-only listing). Sorts by the HH:MM column,
# so it assumes all files were saved on the same day, which is true for a quiz zip.
O["cmd_zip_dates"] = r"""tar -tvf app.zip | Sort-Object { ($_ -split '\s+')[7] } | Select-Object -Last 10"""
