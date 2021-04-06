const path = require('path');

module.exports = {
    watch: true,
    entry: './src/index.js',
    mode: 'development',
    output: {
        path: path.resolve(__dirname, "public/static"),
        filename: "index.js"
    },
    module: {
        rules: [
            {
                test: /\.js$/,
                exclude: /node_modules/,
                loader: "babel-loader"
            }, {
                test: /\.(png|svg|jpe?g|gif|ico)$/,
                loader: 'file-loader',
            }, {
                test: /\.css$/,
                loader: 'css-loader',
            }
        ]
    }
};