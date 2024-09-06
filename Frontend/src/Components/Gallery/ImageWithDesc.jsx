import React, { Fragment, useState, useContext, useCallback } from 'react';
import { Container, Row } from 'reactstrap';
import { Breadcrumbs } from '../../AbstractElements';
import SingleImage from './ImageGallery/SingleImage';
import GalleryContext from '../../_helper/Gallery';
import ListOfImageDesc from './ImageGallery/ListOfImgDesc';

const ImageWithDesc = () => {
    const { images, smallImages } = useContext(GalleryContext);
    const initilindex = { index: 0, isOpen: false };
    const [photoIndex, setPhotoIndex] = useState(initilindex);

    const callback = useCallback((photo) => {
        setPhotoIndex(photo);
    });
    
    return (
        <Fragment>
            <Breadcrumbs mainTitle="Gallery Grid With Description" parent="Gallery" title="Gallery Grid With Description" />
            <Container fluid={true}>
                <Row>
                    <ListOfImageDesc smallImages={smallImages} setPhotoIndex={callback} photoIndex={photoIndex} withDesc={true} />
                </Row>
            </Container>
            <SingleImage photoIndex={photoIndex} setPhotoIndex={callback} images={images} />
        </Fragment>
    );
};


export default ImageWithDesc;