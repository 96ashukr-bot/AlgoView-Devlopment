import React, { Fragment, useState, useContext, useCallback } from 'react';
import { Container, Row } from 'reactstrap'
import { Breadcrumbs } from '../../../AbstractElements';
import GalleryContext from '../../../_helper/Gallery';
import ListOfImage from './ListOfImages';
import SingleImage from './SingleImage';

const ImageGallery = () => {

    const { images, smallImages } = useContext(GalleryContext);
    const initilindex = { index: 0, isOpen: false }
    const [photoIndex, setPhotoIndex] = useState(initilindex)
    
    const callback = useCallback((photo) => {
        setPhotoIndex(photo)
    })

    return (
        <Fragment>
            <Breadcrumbs mainTitle="Gallery Grid" parent="Gallery" title="Gallery Grid" />
            <Container fluid={true}>
                <Row>
                    <ListOfImage smallImages={smallImages} setPhotoIndex={callback} photoIndex={photoIndex} />
                </Row>
            </Container>
            <SingleImage photoIndex={photoIndex} setPhotoIndex={callback} images={images} />
        </Fragment>
    );
}


export default ImageGallery;