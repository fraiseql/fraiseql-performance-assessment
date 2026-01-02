FROM node:18-alpine

WORKDIR /app

# Copy package files
COPY package*.json ./

# Install dependencies
RUN npm install

# Copy application code
COPY . .

# Build TypeScript
RUN npm run build

EXPOSE 4000

CMD ["npm", "start"]
