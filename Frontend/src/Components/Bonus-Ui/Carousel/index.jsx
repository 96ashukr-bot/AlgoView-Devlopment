import React, { Fragment } from 'react';
import { Container, Row, Col } from 'reactstrap';
import { Breadcrumbs } from '../../../AbstractElements';
import SlickSlider from './SlickSlider';

const Carousels = () => {

    return (
        <Fragment>
            <Breadcrumbs mainTitle="Owl Carousel" parent="Bouns Ui" title="Owl Carousel" />
            <Container fluid={true} className="carousal">
                <Row>
                    <Col sm="12">

                        <SlickSlider slides={5} title='Basic Example' rtl={false} lazyLoad={true} />

                        <SlickSlider slides={3} title='Responsive Example' rtl={false} lazyLoad={true} />

                        <SlickSlider slides={3} title='Center Example' rtl={false} lazyLoad={true} />

                        <SlickSlider slides={3} title='Right to Left Example' rtl={true} lazyLoad={false} />

                        <SlickSlider slides={3} title='Lazy load Example' rtl={false} lazyLoad={true} />

                        <SlickSlider slides={3} title='Auto Play Example' rtl={false} lazyLoad={true} autoplay={true} />

                        <SlickSlider slides={3} title='FocusOnSelect' rtl={false} lazyLoad={true} focusOnSelect={true} />

                    </Col>
                </Row>
            </Container>
        </Fragment>
    );
};

export default Carousels;