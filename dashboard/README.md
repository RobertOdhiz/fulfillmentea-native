# Fulfillmentea Admin Dashboard

A professional Streamlit-based administrative dashboard for managing parcel delivery operations.

## 🏗️ Structure

```
dashboard/
├── app.py                 # Main application entry point
├── config.py             # Configuration settings
├── requirements.txt      # Python dependencies
├── README.md            # This file
├── api/                 # API client and utilities
│   ├── __init__.py
│   └── client.py        # HTTP client with timeout configuration
├── auth/                # Authentication modules
│   ├── __init__.py
│   └── login.py         # Login and auth utilities
└── pages/               # Dashboard page modules
    ├── __init__.py
    ├── overview.py      # Main dashboard overview
    ├── riders.py        # Rider management
    ├── inventory.py     # Inventory management
    ├── staff.py         # Staff management
    ├── receipts.py      # Receipt generation and management
    └── analytics.py     # Performance analytics and charts
```

## 🚀 Features

### 📊 Overview Dashboard
- Real-time KPIs (Total Parcels, Dispatched, Delivered, Failures, Pending)
- Daily parcel volume charts
- Delivery outcome distribution with color coding
- Recent activity timeline

### 🚚 Rider Management
- **Add new riders** with name, phone, and vehicle details
- **Edit existing riders** (name, phone, vehicle details)
- **Delete/deactivate riders** (soft delete)
- View all riders in organized table

### 📦 Inventory Management
- **Add new inventory items** with SKU, quantity, and unit
- **Adjust quantities** (add/subtract from current stock)
- **Deactivate items** (soft delete)
- Real-time inventory tracking

### 👥 Staff Management
- **Add new staff members** with roles and permissions
- **Edit staff details** (name, phone, email, role, password)
- **Delete/deactivate staff** (soft delete)
- Role-based access control
- Staff performance metrics

### 🧾 Receipt Management
- **Generate receipts** for any parcel
- **Print receipts** using browser print dialog (POS compatible)
- **Bulk printing** for multiple receipts
- Receipt history and statistics
- Print instructions for POS integration

### 📈 Analytics & Performance
- **Delivery performance analysis** with success rate trends
- **Staff performance metrics** by role and individual
- **Time analysis** for delivery efficiency
- **Financial analysis** with revenue and profit margins
- Interactive charts and visualizations

## 🔐 Authentication & Security

- JWT-based authentication
- Role-based access control (ADMIN, SUPER_ADMIN, MANAGER)
- Secure password handling
- Session management

## 🖨️ POS Integration

The dashboard includes built-in POS printer support:
- Browser-based printing (Ctrl+P / Cmd+P)
- Receipt formatting optimized for thermal printers
- Bulk printing capabilities
- Print instructions for staff

## ⚙️ Configuration

### Environment Variables
```bash
API_BASE_URL=http://localhost:8000  # Backend API URL
```

### Request Timeouts
- Default timeout: 30 seconds
- Configurable in `config.py`

## 🚀 Running the Dashboard

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Set environment variables:**
   ```bash
   export API_BASE_URL="http://localhost:8000"
   ```

3. **Run the dashboard:**
   ```bash
   streamlit run app.py
   ```

4. **Access the dashboard:**
   - URL: http://localhost:8501
   - Login with admin credentials

## 📱 Mobile Responsiveness

The dashboard is optimized for:
- Desktop screens (primary)
- Tablet devices
- Mobile browsers (basic functionality)

## 🔧 Customization

### Adding New Pages
1. Create a new module in `pages/`
2. Implement a `render_*()` function
3. Add to the navigation menu in `app.py`

### Modifying Charts
- Uses Plotly Express for interactive charts
- Easy to customize colors, layouts, and data sources
- Export capabilities built-in

### API Integration
- Centralized API client in `api/client.py`
- Configurable timeouts and error handling
- Easy to extend for new endpoints

## 🐛 Troubleshooting

### Common Issues
1. **Import errors**: Ensure all modules use absolute imports
2. **API timeouts**: Increase `REQUEST_TIMEOUT` in `config.py`
3. **Authentication errors**: Check backend connectivity and JWT tokens

### Logs
- Streamlit logs are displayed in the terminal
- API errors are shown in the UI with helpful messages

## 📈 Performance

- Lazy loading of data
- Efficient database queries
- Optimized chart rendering
- Responsive UI updates

## 🔒 Security Features

- JWT token validation
- Role-based access control
- Secure password handling
- Session timeout management
- Input validation and sanitization
