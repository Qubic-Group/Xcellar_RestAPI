# How to Upload and Send Package Images

## Overview
The `parcel_images` field in the Order model stores a **list of image URLs**, not the actual image files. You need to upload images first to get URLs, then include those URLs when creating an order.

## Step-by-Step Process

### 1. Upload Images (Up to 5 images per order)

**Endpoint:** `POST /api/v1/orders/upload-image/`

**Headers:**
```
Authorization: Bearer YOUR_ACCESS_TOKEN
Content-Type: multipart/form-data
```

**Request Body (form-data):**
```
image: [binary file]
```

**Response:**
```json
{
  "status": 201,
  "message": "Image uploaded successfully",
  "image_url": "http://localhost:8000/media/orders/parcels/abc123def456.jpg"
}
```

**Example using curl:**
```bash
curl -X POST http://localhost:8000/api/v1/orders/upload-image/ \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "image=@/path/to/package-image.jpg"
```

**Example using JavaScript (fetch):**
```javascript
const formData = new FormData();
formData.append('image', imageFile);

const response = await fetch('http://localhost:8000/api/v1/orders/upload-image/', {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${accessToken}`
  },
  body: formData
});

const data = await response.json();
const imageUrl = data.image_url;
```

### 2. Collect Image URLs

Upload each image (max 5) and collect the URLs:
```javascript
const imageUrls = [];
for (const imageFile of selectedImages) {
  const url = await uploadImage(imageFile);
  imageUrls.push(url);
}
```

### 3. Create Order with Image URLs

**Endpoint:** `POST /api/v1/orders/create/`

**Request Body:**
```json
{
  "pickup_address": "123 Main St",
  "pickup_latitude": "6.5244",
  "pickup_longitude": "3.3792",
  "dropoff_address": "456 Oak Ave",
  "dropoff_latitude": "6.5244",
  "dropoff_longitude": "3.3792",
  "recipient_name": "John Doe",
  "recipient_email": "john@example.com",
  "recipient_phone": "+1234567890",
  "parcel_type": "ELECTRONICS",
  "parcel_description": "Laptop and accessories",
  "parcel_condition": "Good",
  "parcel_quantity": 1,
  "parcel_weight_kg": "2.5",
  "parcel_financial_worth": "1500.00",
  "parcel_images": [
    "http://localhost:8000/media/orders/parcels/image1.jpg",
    "http://localhost:8000/media/orders/parcels/image2.jpg"
  ],
  "delivery_fee": "500.00",
  "service_charge": "50.00",
  "insurance_fee": "25.00",
  "total_amount": "575.00"
}
```

## Image Requirements

- **Allowed formats:** JPG, JPEG, PNG, GIF, WEBP
- **Maximum size:** 5MB per image
- **Maximum images per order:** 5 images
- **Authentication:** Required (USER type only)

## Complete Example Flow

```javascript
// 1. Upload images
const uploadImage = async (file) => {
  const formData = new FormData();
  formData.append('image', file);
  
  const response = await fetch('/api/v1/orders/upload-image/', {
    method: 'POST',
    headers: { 'Authorization': `Bearer ${token}` },
    body: formData
  });
  
  const data = await response.json();
  return data.image_url;
};

// 2. Upload multiple images
const images = [file1, file2, file3];
const imageUrls = await Promise.all(images.map(uploadImage));

// 3. Create order with image URLs
const orderData = {
  pickup_address: "123 Main St",
  // ... other fields
  parcel_images: imageUrls  // List of uploaded image URLs
};

const response = await fetch('/api/v1/orders/create/', {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${token}`,
    'Content-Type': 'application/json'
  },
  body: JSON.stringify(orderData)
});
```

