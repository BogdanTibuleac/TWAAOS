## Swagger Screenshots

### Overview of all endpoints
Displays all available routes (GET, POST, PUT, DELETE) exposed by the API.
![Overview](./images/Picture1.png)

### Successful product creation (201 Created)
Shows a valid POST request and the returned product payload.
![Create Success](./images/Picture2.png)

### Duplicate product error (400 Bad Request)
Demonstrates validation when attempting to create a product with an existing ID.
![Create Error](./images/Picture3.png)

### Filter products by stock
Example of using query parameter `stoc_minim` to filter results.
![Filter](./images/Picture4.png)

### Retrieve all products (GET)
Returns the full list of products stored in memory.
![Get All](./images/Picture5.png)

### Retrieve product by ID (GET)
Fetches a specific product using its unique identifier.
![Get One](./images/Picture6.png)

### Update product (PUT)
Replaces an existing product with new data.
![Update](./images/Picture7.png)

### Delete product (DELETE)
Removes a product and returns the deleted entity.
![Delete](./images/Picture8.png)

### Final state after operations
Shows the updated inventory after multiple operations.
![Final State](./images/Picture9.png)