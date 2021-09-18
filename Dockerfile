FROM node:16-alpine3.11
EXPOSE 3000
WORKDIR /core
ENV PATH="./node_modules/.bin:$PATH"
COPY . .
RUN npm run build
CMD ["npm", "start"]