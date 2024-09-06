import React, { Fragment } from 'react';
import { Card, CardBody, Col } from 'reactstrap';
import { Image } from '../../../AbstractElements';
import { IMAGE_GALLERY } from '../../../Constant';
import HeaderCard from '../../Common/Component/HeaderCard';

const ListOfImage = ({ smallImages, setPhotoIndex, photoIndex, withDesc }) => {
  return (
    <Fragment>
      {smallImages.length > 0 ? (
        <Col sm='12'>
          <Card>
            <HeaderCard title={IMAGE_GALLERY} />
            <CardBody>
              <div className='my-gallery row'>
                <figure className='col-xl-3 col-sm-6'>
                  <Image attrImage={{ src: require(`../../../assets/images/${smallImages[0]}`), alt: 'Gallery', className: 'img-thumbnail', onClick: () => setPhotoIndex({ ...photoIndex, index: 0, isOpen: true }) }} />
                </figure>
                <figure className='col-xl-3 col-sm-6'>
                  <Image attrImage={{ src: require(`../../../assets/images/${smallImages[2]}`), alt: 'Gallery', className: 'img-thumbnail', onClick: () => setPhotoIndex({ ...photoIndex, index: 2, isOpen: true }) }} />
                </figure>
                <figure className='col-xl-3 col-sm-6'>
                  <Image attrImage={{ src: require(`../../../assets/images/${smallImages[1]}`), alt: 'Gallery', className: 'img-thumbnail', onClick: () => setPhotoIndex({ ...photoIndex, index: 1, isOpen: true }) }} />
                </figure>
                <figure className='col-xl-3 col-sm-6'>
                  <Image attrImage={{ src: require(`../../../assets/images/${smallImages[3]}`), alt: 'Gallery', className: 'img-thumbnail', onClick: () => setPhotoIndex({ ...photoIndex, index: 3, isOpen: true }) }} />
                </figure>
                <figure className='col-xl-3 col-sm-6'>
                  <Image attrImage={{ src: require(`../../../assets/images/${smallImages[8]}`), alt: 'Gallery', className: 'img-thumbnail', onClick: () => setPhotoIndex({ ...photoIndex, index: 8, isOpen: true }) }} />
                </figure>
                <figure className='col-xl-3 col-sm-6'>
                  <Image attrImage={{ src: require(`../../../assets/images/${smallImages[5]}`), alt: 'Gallery', className: 'img-thumbnail', onClick: () => setPhotoIndex({ ...photoIndex, index: 5, isOpen: true }) }} />
                </figure>
                <figure className='col-xl-3 col-sm-6'>
                  <Image attrImage={{ src: require(`../../../assets/images/${smallImages[4]}`), alt: 'Gallery', className: 'img-thumbnail', onClick: () => setPhotoIndex({ ...photoIndex, index: 4, isOpen: true }) }} />
                </figure>
                <figure className='col-xl-3 col-sm-6'>
                  <Image attrImage={{ src: require(`../../../assets/images/${smallImages[9]}`), alt: 'Gallery', className: 'img-thumbnail', onClick: () => setPhotoIndex({ ...photoIndex, index: 9, isOpen: true }) }} />
                </figure>
                <figure className='col-xl-3 col-sm-6'>
                  <Image attrImage={{ src: require(`../../../assets/images/${smallImages[6]}`), alt: 'Gallery', className: 'img-thumbnail', onClick: () => setPhotoIndex({ ...photoIndex, index: 6, isOpen: true }) }} />
                </figure>
                <figure className='col-xl-3 col-sm-6'>
                  <Image attrImage={{ src: require(`../../../assets/images/${smallImages[7]}`), alt: 'Gallery', className: 'img-thumbnail', onClick: () => setPhotoIndex({ ...photoIndex, index: 7, isOpen: true }) }} />
                </figure>
                <figure className='col-xl-3 col-sm-6'>
                  <Image attrImage={{ src: require(`../../../assets/images/${smallImages[11]}`), alt: 'Gallery', className: 'img-thumbnail', onClick: () => setPhotoIndex({ ...photoIndex, index: 11, isOpen: true }) }} />
                </figure>
                <figure className='col-xl-3 col-sm-6'>
                  <Image attrImage={{ src: require(`../../../assets/images/${smallImages[10]}`), alt: 'Gallery', className: 'img-thumbnail', onClick: () => setPhotoIndex({ ...photoIndex, index: 10, isOpen: true }) }} />
                </figure>
              </div>
            </CardBody>
          </Card>
        </Col>
      ) : (
        ''
      )}
    </Fragment>
  );
};

export default ListOfImage;
