import ProductContext from "../../../../_helper/Ecommerce/Product";
import CartContext from "../../../../_helper/Ecommerce/Cart";
import { H4, LI, P, Image, UL } from "../../../../AbstractElements";
import FilterContext from "../../../../_helper/Ecommerce/Filter";
import { getVisibleproducts } from "../../../../Services/Ecommerce.service";
import ProductModal from "./ProductModal";
import React, { Fragment, useContext, useState } from "react";
import { Link } from "react-router-dom";
import { useNavigate } from "react-router";
import { Row, Card, Button } from "reactstrap";
import CustomizerContext from "../../../../_helper/Customizer";

const ProductGrid = () => {
  const { addToCart } = useContext(CartContext);
  const { productItem, symbol } = useContext(ProductContext);
  const layoutColumns = 3;
  const { layoutURL } = useContext(CustomizerContext);

  const quantity = 1;
  const [dataid, setDataid] = useState("");
  const [openModal, setOpenModal] = useState(false);
  const history = useNavigate();

  const AddToCarts = (item, quantity) => {
    addToCart(item, quantity);
    history(`/app/ecommerce/cart/${layoutURL}`);
  };

  const onOpenModal = (productId) => {
    setOpenModal(true);
    setDataid(productId);
  };

  const addWishList = () => {
    history(`/app/ecommerce/wishlist/${layoutURL}`);
  };
  var images = require.context("../../../../assets/images", true);
  const dynamicImage = (image) => {
    return images(`./${image}`);
  };
  const context = useContext(FilterContext);
  const products = getVisibleproducts(productItem, context.filter);

  return (
    <Fragment>
      <div className="product-wrapper-grid" id="product-wrapper-grid">
        <Row className="gridRow" id="gridRow">
          {products &&
            products.map((item) => {
              return (
                <div id="gridId" className={`${layoutColumns === 3 ? "col-xl-3 col-lg-6 col-sm-6 xl-4 box-col-4" : "col-xl-" + layoutColumns}`} key={item.id}>
                  <Card>
                    <div className="product-box">
                      <div className="product-img">
                        {item.status === "sale" ? <span className="ribbon ribbon-danger">{item.status}</span> : ""}
                        {item.status === "50%" ? <span className="ribbon ribbon-success ribbon-right">{item.status}</span> : ""}
                        {item.status === "gift" ? (
                          <span className="ribbon ribbon-secondary ribbon-vertical-left">
                            <i className="icon-gift">{item.status}</i>
                          </span>
                        ) : (
                          ""
                        )}
                        {item.status === "love" ? (
                          <span className="ribbon ribbon-bookmark ribbon-vertical-right ribbon-info">
                            <i className="icon-heart">{item.status}</i>
                          </span>
                        ) : (
                          ""
                        )}
                        {item.status === "Hot" ? <span className="ribbon ribbon ribbon-clip ribbon-warning">{item.status}</span> : ""} <Image attrImage={{ className: "img-fluid", src: `${dynamicImage(item.img)}`, alt: "" }} />
                        <div className="product-hover">
                          <UL attrUL={{ className: "simple-list d-flex flex-row" }}>
                            <LI attrLI={{ className: "border-0" }}>
                              {/* <Link to={`/app/ecommerce/cart/${layoutURL}`}> */}
                              <Button color="default" onClick={() => AddToCarts(item, quantity)}>
                                <i className="icon-shopping-cart"></i>
                              </Button>
                              {/* </Link> */}
                            </LI>
                            <LI attrLI={{ className: "border-0" }}>
                              <Button color="default" data-toggle="modal" onClick={() => onOpenModal(item.id)}>
                                <i className="icon-eye"></i>
                              </Button>
                            </LI>
                            <LI attrLI={{ className: "border-0" }}>
                              <Link to={`/app/ecommerce/wishlist/${layoutURL}`}>
                                <Button color="default" onClick={() => addWishList(item)}>
                                  <i className="icon-heart"></i>
                                </Button>
                              </Link>
                            </LI>
                          </UL>
                        </div>
                      </div>
                      <div className="product-details">
                        <div className="rating">
                          <i className="fa fa-star font-warning"></i>
                          <i className="fa fa-star font-warning"></i>
                          <i className="fa fa-star font-warning"></i>
                          <i className="fa fa-star font-warning"></i>
                          <i className="fa fa-star font-warning"></i>
                        </div>
                        <Link to={`/app/ecommerce/product-page/${layoutURL}/${item.id}`}>
                          <H4>{item.name}</H4>
                        </Link>

                        <P>{item.note}</P>
                        <div className="product-price">
                          {symbol} {item.price}{" "}
                          <del>
                            {symbol} {item.discountPrice}
                          </del>
                        </div>
                      </div>
                    </div>
                  </Card>
                </div>
              );
            })}
          {openModal && <ProductModal value={openModal} setOpenModal={setOpenModal} dataid={dataid} />}
        </Row>
      </div>
    </Fragment>
  );
};
export default ProductGrid;
