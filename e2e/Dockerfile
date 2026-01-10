FROM mcr.microsoft.com/playwright:v1.41.1-jammy

WORKDIR /app

# Copy package files
COPY package.json ./

# Install dependencies
RUN npm install

# Copy test files
COPY . .

# Run tests
CMD ["npm", "test"]
