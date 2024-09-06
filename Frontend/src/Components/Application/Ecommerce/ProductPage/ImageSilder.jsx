import React, { useContext, useEffect, useRef, useState } from 'react';
import ProductContext from '../../../../_helper/Ecommerce/Product';
import { Image } from '../../../../AbstractElements';
import { Fragment } from 'react';
import Slider from 'react-slick';
import { Media } from 'reactstrap';

const ImageSlider = () => {
  const { productItem } = useContext(ProductContext);
  const [state, setState] = useState({ nav1: null, nav2: null });
  const slider1 = useRef();
  const slider2 = useRef();
  useEffect(() => {
    setState({
      nav1: slider1.current,
      nav2: slider2.current,
    });
  }, []);
  const { nav1, nav2 } = state;
  var images = require.context('../../../../assets/images', true);
  const dynamicImage = (image) => {
    return images(`./${image}`);
  };
  return (
    <Fragment>
      <Slider asNavFor={nav2} className='product-slider' arrows={false} ref={(slider) => (slider1.current = slider)}>
        {productItem ? (
          productItem.map((item) => {
            return item.variants.map((items, id) => (
              <Image
                attrImage={{
                  src: `${dynamicImage(items.images)}`,
                  alt: '',
                  className: 'img-fluid w-100',
                }}
                key={id}
              />
            ));
          })
        ) : (
          <Media src={productItem.img} alt='' className='img-fluid' />
        )}
      </Slider>
      <Slider asNavFor={nav1} ref={(slider) => (slider2.current = slider)}  slidesToShow={4} swipeToSlide={true} focusOnSelect={true} infinite={true} className='small-slick'>
        {productItem &&
          productItem.map((item) => {
            return item.variants.map((items, id) => (
              <Image
                attrImage={{
                  src: `${dynamicImage(items.images)}`,
                  alt: '',
                  className: 'img-fluid item',
                }}
                key={id}
              />
            ));
          })}
      </Slider>
    </Fragment>
  );
};
export default ImageSlider;
