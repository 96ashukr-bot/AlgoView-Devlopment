import React, { Fragment, useContext } from "react";
import { CartTitle, CartTableHeader } from "../../../../Constant";
import { getCartTotal } from "../../../../Services/Ecommerce.service";
import { Btn, H6, Image } from "../../../../AbstractElements";
import { CardBody, Table, Row, Input } from "reactstrap";
import { Link } from "react-router-dom";
import { XCircle } from "react-feather";
import ProductContext from "../../../../_helper/Ecommerce/Product";
import CartContext from "../../../../_helper/Ecommerce/Cart";
import EmptyCart from "./EmptyCart";
import HeaderCard from "../../../Common/Component/HeaderCard";
import CustomizerContext from "../../../../_helper/Customizer";

const CartData = () => {
  const { layoutURL } = useContext(CustomizerContext);
  const { symbol } = useContext(ProductContext);
  const { addToCart, cart, decrementQty, removeFromCart } = useContext(CartContext);
  const incrementQty = (product, quantity) => {
    addToCart(product, quantity);
  };
  const decrementQuantity = (id) => {
    decrementQty(id);
  };
  const removefromcart = (item) => {
    removeFromCart(item.id);
  };
  var images = require.context("../../../../assets/images", true);
  const dynamicImage = (image) => {
    return images(`./${image}`);
  };

  return (
    <Fragment>
      {cart && cart.length > 0 ? (
        <div>
          <HeaderCard title={CartTitle} />
          <CardBody className="cart">
            <Row>
              <div className="order-history table-responsive wishlist">
                <Table className="table-bordered">
                  <thead>
                    <tr>
                      {CartTableHeader.map((items, i) => (
                        <th key={i}>{items}</th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {cart.map((item, i) => {
                      return (
                        <tr key={i}>
                          <td>
                            <Image attrImage={{ className: "img-fluid img-60", src: `${dynamicImage(item.imgPng)}`, alt: "#" }} />
                          </td>
                          <td>
                            <div className="product-name">
                              <a href="#javascript">{item.name}</a>
                            </div>
                          </td>
                          <td>${item.price}</td>
                          <td className="qty-box">
                            <div className="input-group bootstrap-touchspin">
                              <span className="input-group-prepend">
                                <Btn
                                  attrBtn={{
                                    color: "primary",
                                    className: "bootstrap-touchspin-down btn-square",
                                    onClick: () => decrementQuantity(item.id),
                                  }}>
                                  <i className="fa fa-minus"></i>
                                </Btn>
                              </span>
                              <Input type="text" name="quantity" value={item.qty} readOnly={true} style={{ textAlign: "center" }} className="form-control input-number" />
                              <span className="input-group-append">
                                <Btn attrBtn={{ color: "primary", className: "bootstrap-touchspin-up btn-square", onClick: () => incrementQty(item, 1) }}>
                                  {" "}
                                  <i className="fa fa-plus"></i>
                                </Btn>{" "}
                              </span>
                            </div>
                          </td>
                          <td>
                            <a href="#javascript" onClick={() => removefromcart(item)}>
                              <XCircle />
                            </a>
                          </td>
                          <td>
                            {symbol}
                            {item.price * item.qty}
                          </td>
                        </tr>
                      );
                    })}
                    <tr>
                      <td colSpan="4">
                        <div className="input-group">
                          <Input className="form-control me-2" type="text" placeholder="Enter coupan code" />
                          <a className="btn btn-primary" href="#javascript">
                            Apply
                          </a>
                        </div>
                      </td>
                      <td className="total-amount">
                        <H6 attrH6={{ className: "m-0 text-end" }}>
                          <span className="f-w-600">Total Price :</span>
                        </H6>
                      </td>
                      <td>
                        <span>${getCartTotal(cart)}</span>
                      </td>
                    </tr>
                    <tr>
                      <td className="text-end" colSpan="5">
                        <Link to={`/app/ecommerce/product/${layoutURL}`} className="btn btn-secondary cart-btn-transform">
                          continue shopping
                        </Link>
                      </td>
                      <td>
                        <Link className="btn btn-success cart-btn-transform" to={`/app/ecommerce/checkout/${layoutURL}`}>
                          check out
                        </Link>
                      </td>
                    </tr>
                  </tbody>
                </Table>
              </div>
            </Row>
          </CardBody>
        </div>
      ) : (
        <EmptyCart />
      )}
    </Fragment>
  );
};
export default CartData;
