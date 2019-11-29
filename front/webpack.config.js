const HtmlWebPackPlugin = require('html-webpack-plugin')
const path = require('path')

module.exports = {
  context: __dirname,
  entry: './src/index.js',
  mode: 'development',
  devServer: {
    contentBase: './dist',
    historyApiFallback: true
  },
  output: {
    path: path.resolve(__dirname, '/dist'),
    filename: 'main.js',
    publicPath: '/'
  },
  watch: true,
  module: {
    rules: [
      {
        test: /\.(js|jsx)$/,
        exclude: /node_modules/,
        use: {
          loader: 'babel-loader'
        }
      },
      {
        test: /\.svg$/,
        loader: 'url-loader'
      },
      {
        test: /\.html$/,
        use: [
          {
            loader: 'html-loader'
          }
        ]
      },
      {
        test: /\.(woff|woff2|eot|ttf|otf|jpg|png)$/,
        use: [
          {
            loader: 'file-loader',
            options: {
              outputPath: 'assets',
              publicPath: 'assets'
            }
          }
        ]
      },
      {
        test: /\.(s[ac]ss|css)$/i,
        use: ['style-loader', 'css-loader', 'sass-loader']
      }
    ]
  },
  resolve: {
    extensions: ['.js', '.jsx']
  },
  plugins: [
    new HtmlWebPackPlugin({
      template: './src/index.ejs'
    })
  ]
}
