FROM node:20-alpine
WORKDIR /app
COPY package.json tsconfig.json ./
RUN npm i
COPY src ./src
RUN npm run build
EXPOSE 8000
ENV PORT=8000
CMD ["node", "dist/index.js"]