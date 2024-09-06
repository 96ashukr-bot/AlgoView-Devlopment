import ProductContext from '../../../../_helper/Ecommerce/Product';
import { Price, MoveToCarts } from '../../../../Constant';
import CartContext from '../../../../_helper/Ecommerce/Cart';
import { Btn, H6, Image } from '../../../../AbstractElements';
import { useNavigate } from 'react-router';
import { Col, Media } from 'reactstrap';
import React, { Fragment, useContext } from 'react';
import CustomizerContext from '../../../../_helper/Customizer';

const WishListData = () => {
  const history = useNavigate();
  const { layoutURL } = useContext(CustomizerContext);
  const { productItem, symbol } = useContext(ProductContext);
  const { addToCart } = useContext(CartContext);

  const MoveToCart = (product, qty) => {
    addToCart(product, qty);
    history(`/app/ecommerce/cart/${layoutURL}`);
  };
  var images = require.context('../../../../assets/images', true);
  const dynamicImage = (image) => {
    return images(`./${image}`);
  };
  return (
    <Fragment>
      {productItem.map((item) => {
        return (
          <Col key={item.id} xl='4' md='6'>
            <div className='prooduct-details-box'>
              <Media>
                <Image attrImage={{ className: 'align-self-center img-fluid img-60 border-0', src: `${dynamicImage(item.imgPng)}`, alt: '#' }} />
                <div className='media-body ms-3'>
                  <div className='product-name'>
                    <H6>
                      <a href='3'>{item.name}</a>
                    </H6>
                  </div>
                  <div className='rating'>
                    <i className='fa fa-star'></i>
                    <i className='fa fa-star'></i>
                    <i className='fa fa-star'></i>
                    <i className='fa fa-star'></i>
                    <i className='fa fa-star'></i>
                  </div>
                  <div className='price'>
                    {Price}
                    <span>
                      : {item.price}
                      {symbol}
                    </span>
                  </div>
                  <div className='avaiabilty'>
                    <div className='text-success'>{item.stock}</div>
                  </div>
                  <Btn
                    attrBtn={{
                      color: 'primary',
                      size: 'xs',
                      onClick: () => MoveToCart(item, 1),
                    }}>
                    {MoveToCarts}
                  </Btn>
                </div>
              </Media>
            </div>
          </Col>
        );
      })}
    </Fragment>
  );
};
export default WishListData;
