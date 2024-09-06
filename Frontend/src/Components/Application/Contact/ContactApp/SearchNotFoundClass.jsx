import React, { Fragment } from 'react';
import { Col } from 'reactstrap';
import { Image, P } from '../../../../AbstractElements';
import search from '../../../../assets/images/search-not-found.png';

const SearchNotFoundClass = () => {
    return (
        <Fragment>
            <Col sm="12">
                <div>
                    <div className="search-not-found text-center">
                        <div>
                            <Image attrImage={{ src: `${search}`, alt: '', className: 'second-search' }} />
                            <P attrPara={{ className: 'mb-2' }} >{'Sorry, Not Found Any Contact'}</P>
                        </div >
                    </div >
                </div >
            </Col >
        </Fragment >
    );
};

export default SearchNotFoundClass;