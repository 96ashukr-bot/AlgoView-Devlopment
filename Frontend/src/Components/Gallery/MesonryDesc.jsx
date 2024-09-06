import React, { Fragment, useContext } from 'react';
import Masonry from 'react-masonry-css';
import { Container, Row, Col, Card, CardBody, Media } from 'reactstrap';
import { PortfolioTitle, MasonryGalleryWithDescription } from '../../Constant';
import { Breadcrumbs, H4, P } from '../../AbstractElements';
import GalleryContext from '../../_helper/Gallery';
import HeaderCard from '../Common/Component/HeaderCard';

const MesonryDesc = () => {
    const { masonryImg } = useContext(GalleryContext);
    const breakpointColumnsObj = {
        default: 4,
        1199: 3,
        700: 2,
        500: 1
    };

    return (
      <Fragment>
        <Breadcrumbs mainTitle='Masonry Gallery With Description' parent='Gallery' title='Masonry Gallery With Description' />
        <Container fluid={true}>
          <Row>
            <Col sm='12'>
              <Card>
                <HeaderCard title={MasonryGalleryWithDescription} />
                <CardBody className='photoswipe-pb-responsive'>
                  <Masonry breakpointCols={breakpointColumnsObj} className='my-masonry-grid masonry-with-dec my-gallery gallery-with-description row grid' columnClassName='col-xl-3 col-sm-6 col-md-4 grid-item'>
                    {masonryImg.map((element, index) => (
                      <li style={{ listStyle: 'none' }} key={index}>
                        <a href='#javascript' data-size='1600x950'>
                          <Media src={require(`../../assets/images/${element.src}`)} className='img-thumbnail' style={{ width: '100%' }} alt='' />
                          <div className='caption'>
                            <H4>{PortfolioTitle}</H4>
                            <P>{"is simply dummy text of the printing and typesetting industry. Lorem Ipsum has been the industry's standard dummy."}</P>
                          </div>
                        </a>
                      </li>
                    ))}
                  </Masonry>
                </CardBody>
              </Card>
            </Col>
          </Row>
        </Container>
      </Fragment>
    );
};

export default MesonryDesc;