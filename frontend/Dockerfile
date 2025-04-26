# frontend/Dockerfile
FROM node:20-slim

WORKDIR /app

COPY package*.json ./
RUN npm install

COPY . .

# frontend/Dockerfile
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0"]  # Añade --host 0.0.0.0CMD ["npm", "run", "dev"]
