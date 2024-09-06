import React, { Fragment, useContext, useEffect, useState } from "react";
import { H3, LI, P, UL } from "../../../../AbstractElements";
import { Brand, Availability, AddToCart, BuyNow } from "../../../../Constant";
import ProductContext from "../../../../_helper/Ecommerce/Product";
import WishtListContext from "../../../../_helper/Ecommerce/Wishlist";
import SocialIcons from "./SocialIcons";
import StarRatings from "./StarRating";
import { Row, Col, Card, CardBody, Button } from "reactstrap";
import { Link, useNavigate } from "react-router-dom";
import CartContext from "../../../../_helper/Ecommerce/Cart";
import CustomizerContext from "../../../../_helper/Customizer";

const ProductDetails = () => {
  const { layoutURL } = useContext(CustomizerContext);

  const { productItem, symbol } = useContext(ProductContext);
  const { addToCart } = useContext(CartContext);
  const [productss, setProductss] = useState("");
  const path = window.location.pathname.split("/").pop();

  useEffect(() => {
    productItem.map((item) => {
      if (item.id === path) {
        setProductss(item);
      }
      return null;
    });
  });

  const quantity = 1;
  const history = useNavigate();
  const { addToWishList } = useContext(WishtListContext);

  const singleItem = productItem;
  const addWishList = (product) => {
    addToWishList(product);
    history(`/app/ecommerce/wishlist/${layoutURL}`);
  };

  const AddToCarts = (item, quantity) => {
    addToCart(item, quantity);
    history(`/app/ecommerce/cart/${layoutURL}`);
  };

  const buyProduct = (item, quantity) => {
    addToCart(item, quantity);
  };

  return (
    <Fragment>
      <Col xxl="5" className="box-col-6 order-xxl-0 order-1">
        <Card>
          <CardBody>
            <div className="product-page-details">
              <H3>{"Women Pink shirt."}</H3>
            </div>
            <div className="product-price">
              {symbol}
              {"100"}
              <del>
                {symbol}
                {"350.00"}
              </del>
            </div>
            <UL attrUL={{ className: "product-color flex-row" }}>
              <LI attrLI={{ className: "bg-primary" }}></LI>
              <LI attrLI={{ className: "bg-secondary" }}></LI>
              <LI attrLI={{ className: "bg-success" }}></LI>
              <LI attrLI={{ className: "bg-info" }}></LI>
              <LI attrLI={{ className: "bg-warning" }}></LI>
            </UL>
            <hr />
            <P>{"It is a long established fact that a reader will be distracted by the readable content of a page when looking at its layout. The point of using Lorem Ipsum is that."}</P>
            <hr />
            <div>
              <table className="product-page-width">
                <tbody>
                  <tr>
                    <td>
                      <b>{Brand} &nbsp;&nbsp;&nbsp;:</b>
                    </td>
                    <td>{"Pixelstrap"}</td>
                  </tr>
                  <tr>
                    <td>
                      <b>{Availability} &nbsp;&nbsp;&nbsp;: &nbsp;&nbsp;&nbsp;</b>
                    </td>
                    <td className="txt-success">{"in stock"}</td>
                  </tr>
                  <tr>
                    <td>
                      <b>{"Seller"} &nbsp;&nbsp;&nbsp;: &nbsp;&nbsp;&nbsp;</b>
                    </td>
                    <td>{"ABC"}</td>
                  </tr>
                  <tr>
                    <td>
                      <b>{"Fabric"} &nbsp;&nbsp;&nbsp;: &nbsp;&nbsp;&nbsp;</b>
                    </td>
                    <td>{"Cotton"}</td>
                  </tr>
                </tbody>
              </table>
            </div>
            <hr />
            <Row>
              <SocialIcons />
            </Row>
            <hr />
            <Row>
              <Col md="4">
                <h6 className="product-title">{"Rate Now"}</h6>
              </Col>
              <Col md="8">
                <StarRatings />
              </Col>
            </Row>
            <hr />
            <div>
              <Button color="primary" className="m-r-10 m-t-10" onClick={() => AddToCarts(singleItem[0], quantity)}>
                <i className="fa fa-shopping-basket me-1"></i>
                {AddToCart}
              </Button>
              <Link to={`/app/ecommerce/checkout/${layoutURL}`}>
                <Button color="success" className="m-r-10 m-t-10" onClick={() => buyProduct(productss, quantity)}>
                  <i className="fa fa-shopping-cart me-1"></i>
                  {BuyNow}
                </Button>
              </Link>
              <Button color="secondary" className="m-t-10" onClick={() => addWishList(singleItem)}>
                <i className="fa fa-heart me-1"></i>
                {"Add To WishList"}
              </Button>
            </div>
          </CardBody>
        </Card>
      </Col>
    </Fragment>
  );
};
export default ProductDetails;
