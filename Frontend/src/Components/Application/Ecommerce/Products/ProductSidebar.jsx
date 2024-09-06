import { H6, Image } from '../../../../AbstractElements';
import FilterContext from '../../../../_helper/Ecommerce/Filter';
import Category from '../Filters/Category';
import PrizeRange from '../Filters/PrizeRange';
import banner from '../../../../assets/images/ecommerce/banner.jpg';
import { Card, CardBody, CardHeader, Col, Form, FormGroup, Input, Row } from 'reactstrap';
import React, { Fragment, useContext, useState } from 'react';

const ProductSidebar = () => {
    const { filterContext, filterSearchBy } = useContext(FilterContext);
    const [sidebaron, setSidebaron] = useState(true);
    const [searchKeyword, setSearchKeyword] = useState('');
    const onClickFilter = () => {
        if (sidebaron) {
            setSidebaron(false);
            document.getElementById('product-wrapper').classList.add('sidebaron');
        } else {
            setSidebaron(true);
            document.getElementById('product-wrapper').classList.remove('sidebaron');
        }
    };
    const handleSearchKeyword = (keyword) => {
        setSearchKeyword(keyword);
        filterSearchBy(searchKeyword);
    };
    return (
        <Fragment>
            <Row>
                <Col xl="3" md="6">
                    <div className={`product-sidebar ${filterContext ? 'open' : ''}`}>
                        <div className="filter-section">
                            <Card>
                                <CardHeader>
                                    <H6 attrH6={{ className: 'mb-0 f-w-600' }}>Filters
                                        <span className="pull-right">
                                            <i className="fa fa-chevron-down toggle-data"
                                                onClick={onClickFilter}>
                                            </i>
                                        </span>
                                    </H6>
                                </CardHeader>
                                <div className="left-filter">
                                    <CardBody className="filter-cards-view animate-chk">
                                        <Category />
                                        <PrizeRange />
                                        <div className="product-filter text-center mt-2">
                                            <Image attrImage={{ className: 'img-fluid banner-product m-auto', src: `${banner}`, alt: '' }} />
                                        </div>
                                    </CardBody>
                                </div>
                            </Card>
                        </div>
                    </div>
                </Col>
                <Col xl="9" md="6">
                    <div className="product-search">
                        <Form>
                            <FormGroup className="m-0 form-group search-product">
                                <Input className="form-control" type="text" placeholder="search"
                                    defaultValue={searchKeyword}
                                    onChange={(e) => handleSearchKeyword(e.target.value)} />
                                <i className="fa fa-search"></i>
                            </FormGroup>
                        </Form>
                    </div>
                </Col>
            </Row>
        </Fragment>
    );
};
export default ProductSidebar;