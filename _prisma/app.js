'use strict';

const {App} = require('./index.js');

const prisma = new App();

// A `main` function so that you can use async/await
async function main() {
  const data = await prisma.benchQuery('get_user', 90);
  console.log(data);
  // const data = await prisma.benchQuery('get_person', 120)
  // const data = await prisma.benchQuery('get_movie', 25)
}

main()
  .catch((e) => {
    throw e;
  })
  .finally(async () => {
    await prisma.$disconnect();
  });
