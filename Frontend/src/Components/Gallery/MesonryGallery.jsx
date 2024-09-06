import React, { Fragment, useContext } from 'react';
import Masonry from 'react-masonry-css';
import { Container, Row, Col, Card, CardBody, Media } from 'reactstrap';
import { Breadcrumbs } from '../../AbstractElements';
import { MasonryGallery } from '../../Constant';
import GalleryContext from '../../_helper/Gallery';
import HeaderCard from '../Common/Component/HeaderCard';

const MesonryGallery = () => {

    const { masonryImg } = useContext(GalleryContext);

    return (
        <Fragment>
            <Breadcrumbs mainTitle="Masonry Gallery" parent="Gallery" title="Masonry Gallery" />
            <Container fluid={true}>
                <Row>
                    <Col sm="12">
                        <Card>
                            <HeaderCard title={MasonryGallery} />
                            <CardBody className="photoswipe-pb-responsive">
                                <Masonry
                                    breakpointCols={4}
                                    className="my-gallery row grid gallery"
                                    columnClassName="col-md-3 col-6 grid-item">
                                    {masonryImg.map((element, index) =>
                                        <div key={index} ><Media src={require(`../../assets/images/${element.src}`)} style={{ width: '100%' }} alt="" /></div>
                                    )}
                                </Masonry>
                            </CardBody>
                        </Card>
                    </Col>
                </Row>
            </Container>

        </Fragment>
    );
};

export default MesonryGallery;