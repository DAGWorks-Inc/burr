# run this from the ui/ directory
# ensure your server is running on port 7241 (or change the port below)
# TODO -- move to a package.json script
npx openapi-typescript-codegen --input http://localhost:7241/openapi.json --output ./src/api
