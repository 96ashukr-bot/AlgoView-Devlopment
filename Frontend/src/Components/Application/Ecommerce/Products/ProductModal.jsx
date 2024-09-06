import React, { Fragment, useContext, useEffect, useState } from 'react';
import { Btn, H4, H6, Image, LI, P, UL } from '../../../../AbstractElements';
import { ProductDetails, Quantity, AddToCart, ViewDetails, ProductSizeArray } from '../../../../Constant';
import CartContext from '../../../../_helper/Ecommerce/Cart';
import ProductContext from '../../../../_helper/Ecommerce/Product';
import { Modal, Col, InputGroup, InputGroupText, Input } from 'reactstrap';
import { Link, useNavigate } from 'react-router-dom';
import CustomizerContext from '../../../../_helper/Customizer';

const ProductModal = (props) => {
  const [open, setOpen] = useState(props.value);
  // eslint-disable-next-line
  const [stock, setStock] = useState('');
  const { addToCart } = useContext(CartContext);
  const { layoutURL } = useContext(CustomizerContext);
  const { productItem, symbol } = useContext(ProductContext);
  const [quantity, setQuantity] = useState(1);
  const [singleProduct, setSingleProduct] = useState([]);

  useEffect(() => {
    productItem.forEach((product, i) => {
      if (product.id === props.dataid) {
        setSingleProduct(product);
      }
    });
  }, [productItem, props.dataid]);
  const changeQty = (e) => {
    setQuantity(parseInt(e.target.value));
  };
  const plusQty = () => {
    if (quantity >= 1) {
      setQuantity(quantity + 1);
    } else {
      setStock('Out of Stock !');
    }
  };
  const minusQty = () => {
    if (quantity > 1) {
      setStock('InStock');
      setQuantity(quantity - 1);
    }
  };
  const onCloseModal = () => {
    setOpen(false);
    props.setOpenModal(false);
  };
  const history = useNavigate();
  const AddToCarts = (item, quantity) => {
    addToCart(item, quantity);
    history(`/app/ecommerce/cart/${layoutURL}`);
  };

  return (
    <Fragment>
      <Modal className='modal-dialog modal-lg modal-dialog-centered product-modal' isOpen={open}>
        <div className='modal-body'>
          <div className='modal-header'>
            <div className='modal-title'>
              <div className='product-box row'>
                <Col lg='6'>
                  <Image
                    attrImage={{
                      className: 'img-fluid',
                      src: singleProduct.img ? require('../../../../assets/images/' + singleProduct.img) : '',
                      alt: '',
                    }}
                  />
                </Col>
                <Col lg='6' className='product-details text-start'>
                  <H4>{singleProduct.name}</H4>
                  <div className='product-price'>
                    {symbol}
                    {singleProduct.price}
                    <del>
                      {symbol}
                      {singleProduct.discountPrice}
                    </del>
                  </div>
                  <div className='product-view'>
                    <H6 attrH6={{ className: 'f-w-600' }}>{ProductDetails}</H6>
                    <P attrPara={{ className: 'mb-0' }}>{singleProduct.discription}</P>
                  </div>
                  <div className='product-size'>
                    <UL attrUL={{ className: 'simple-list d-flex gap-1 flex-row' }}>
                      {ProductSizeArray.map((items, i) => (
                        <LI attrLI={{ className: 'border-0' }} key={i}>
                          <Btn attrBtn={{ color: 'outline-light ', type: 'button', databsoriginaltitle: '', title: '' }}>{items}</Btn>
                        </LI>
                      ))}
                    </UL>
                  </div>
                  <div className='product-qnty'>
                    <H6 attrH6={{ className: 'f-w-600' }}>{Quantity}</H6>
                    <fieldset>
                      <InputGroup>
                        <Btn attrBtn={{ color: 'primary', className: 'btn-square bootstrap-touchspin-down', onClick: minusQty }}>
                          <i className='fa fa-minus'></i>
                        </Btn>
                        <InputGroupText className='bootstrap-touchspin-prefix' style={{ display: 'none' }}></InputGroupText>
                        <Input className='touchspin text-center py-0' type='text' name='quantity' value={quantity} onChange={(e) => changeQty(e)} />
                        <Btn attrBtn={{ color: 'primary', className: 'btn-square bootstrap-touchspin-up', onClick: plusQty }}>
                          <i className='fa fa-plus'></i>
                        </Btn>
                      </InputGroup>
                    </fieldset>
                    <div className='addcart-btn'>
                      <Link to={`/app/ecommerce/cart/${layoutURL}`} className='btn btn-primary me-3' onClick={() => AddToCarts(singleProduct, quantity)}>
                        {AddToCart}
                      </Link>
                      <Link to={`/app/ecommerce/product-page/${layoutURL}/${singleProduct.id}`} className='btn btn-primary'>
                        {ViewDetails}
                      </Link>
                    </div>
                  </div>
                </Col>
              </div>
            </div>
            <Btn attrBtn={{ color: 'transprant', className: 'btn-close', onClick: onCloseModal, type: 'button', databsdismiss: 'modal', arialabel: 'Close' }}></Btn>
          </div>
        </div>
      </Modal>
    </Fragment>
  );
};
export default ProductModal;
