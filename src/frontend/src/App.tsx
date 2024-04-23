import { BrowserRouter as Router, Routes, Route } from "react-router-dom";
import { Layout } from "antd";

import { Auth } from "./pages/Auth";
import { Order } from "./pages/Order";
import { OrderDeal } from "./pages/OrderDeal";
import { BookList } from "./pages/BookList";
import Nav from "./components/Nav";
import { AuthProvider } from "./context/AuthContext";
import { CartProvider } from "./context/CartContext";
import "./App.css";

const { Content, Footer } = Layout;

function App() {
  return (
    <Router>
      <AuthProvider>
        <CartProvider>
          <Layout>
            <Nav />

            <Content
              style={{
                padding: "10px 50px",
                minHeight: "85vh",
                margin: "0 120px",
              }}
            >
              <Routes>
                <Route path="/" element={<BookList />} />
                <Route path="/auth" element={<Auth />} />
                {/* <Route path="/cart" element={<Cart />} /> */}
                <Route path="/order" element={<Order />} />
                <Route path="/order/:id" element={<OrderDeal />} />
              </Routes>
            </Content>

            <Footer style={{ textAlign: "center" }}>
              OpenTelemetry Demo ©2023 Created by @Daocloud
            </Footer>
          </Layout>
        </CartProvider>
      </AuthProvider>
    </Router>
  );
}

export default App;
