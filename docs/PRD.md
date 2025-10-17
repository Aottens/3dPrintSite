# 3D Print Site Product Requirements (PRD v1.0)

## 5.3 Default Coefficients

| Parameter | Default | Notes |
|------------|----------|-------|
| Density PLA | 1.24 g/cm³ | adjustable |
| Density PETG | 1.27 g/cm³ | adjustable |
| Density ASA | 1.07 g/cm³ | adjustable |
| Material cost | per g defined by admin | |
| Machine rate | 15 €/h | |
| Base fee | 4 € per order | |
| Post rate | 0.80 €/min | |
| Risk multiplier | 1.10 | |
| Min item | 6 € | |
| Min order | 15 € | |
| Setup time | 0.25 h | minimum billable time |

All coefficients are versioned in **PricingConfig** and editable from the admin dashboard.

## 5.4 Outputs

- `unit_price` (EUR)
- `lead_time_days`
- `breakdown {material, machine, base, post, total}`

---

## 6. Data Model

### 6.1 Core Entities

| Entity | Key Fields |
|---------|-------------|
| **User** | id, name, email, password_hash, role, vat_number, addresses |
| **Material** | id, family, brand, color_name, hex, density, cost_per_kg, surcharge, active |
| **ModelFile** | id, user_id, filename, volume_mm3, surface_mm2, bounding_box, weight_g, upload_url |
| **Quote** | id, user_id, model_id, material_id, quantity, price, config_version |
| **Order** | id, user_id, status, tracking_code, created_at, total_price |
| **OrderItem** | order_id, quote_id, printer_assigned, status |
| **PricingConfig** | id, version, effective_from, parameters(JSON), created_by |
| **PrinterJob** | order_item_id, printer_name, start_time, end_time, duration_hr |

---

## 7. API Endpoints (REST Example)

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/upload` | Upload 3D model |
| GET | `/api/quote` | Calculate quote |
| POST | `/api/order` | Place order |
| GET | `/api/order/:id` | Get order details |
| PATCH | `/api/order/:id/status` | Update order status (admin/operator) |
| GET | `/api/materials` | List available materials/colors |
| POST | `/api/admin/material` | Add/update material |
| GET | `/api/admin/pricing/config` | Get current algorithm config |
| POST | `/api/admin/pricing/config` | Update algorithm coefficients |

---

## 8. UI Components

### Customer Portal
1. **Upload & Quote Page**
   - Drag-and-drop upload zone
   - Model viewer
   - Material / color / infill / layer height selectors
   - Instant quote display and breakdown
2. **Cart & Checkout**
   - Item summary table
   - Address and shipping form
   - Payment integration
3. **Account Dashboard**
   - Order list with statuses and tracking
   - Invoice downloads
   - Profile editor

### Admin Portal
1. **Materials Manager**
   - Table view with search, add, edit, delete
2. **Pricing Config**
   - Editable table of algorithm coefficients
   - Version control and publish button
3. **Orders View**
   - Filter by status, material, printer
   - Update status and assign printer
4. **Analytics Dashboard**
   - Orders per day, revenue, top materials
5. **User Management**
   - View customers, disable accounts

---

## 9. Tech Stack Recommendation

| Layer | Technology |
|--------|-------------|
| Frontend | React (Next.js) + TailwindCSS |
| Backend | Python (FastAPI) |
| Database | PostgreSQL |
| Storage | S3-compatible (minio, AWS S3) |
| Geometry | Python microservice (trimesh / meshio) |
| Payment | Stripe or Mollie |
| Hosting | Vercel (frontend) + Render/AWS (backend) |
| Auth | JWT + bcrypt |
| Logs | Structured JSON logs + admin audit trail |

---

## 10. Acceptance Criteria

1. A new user can upload a valid `.stl`, select a material, and receive a quote within **10 s**.  
2. The admin can add new colors and materials through the dashboard without developer assistance.  
3. Orders follow all defined statuses, and each transition triggers an email notification.  
4. Every quote and order stores its pricing version and exact breakdown.  
5. The website adapts cleanly to mobile, tablet, and desktop layouts.  
6. GDPR export and deletion endpoints return correct data within legal timeframes.  
7. The system can handle 100 concurrent users without quote-time degradation above 15 s.  

---

## 11. Versioning and Extensibility

- Pricing algorithm stored per **version** (`PricingConfig.version`)
- Future additions: new materials, post-processing, batch discounts
- API designed with forward compatibility (JSON-Schema validation)
- All constants and formulas editable from admin panel with rollback capability

---

**End of PRD v1.0**
