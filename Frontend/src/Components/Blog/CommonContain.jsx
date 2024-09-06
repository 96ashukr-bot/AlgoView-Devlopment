import React from 'react';
import { Col, Media, Row } from 'reactstrap';
import { UL, LI, P, H6 } from '../../AbstractElements';

const CommonContain = ({ item }) => {
  return (
    <Media className='align-self-center'>
      <Media className='align-self-center' src={item.src} alt='' />
      <Media body>
        <Row>
          <Col md='4'>
            <H6 attrH6={{ className: 'mt-0' }}>
              {item.name}
              <span> {`( ${item.post} ) `}</span>
            </H6>
          </Col>
          <Col md='8'>
            <UL attrUL={{ className: 'comment-social float-start float-md-end simple-list' }}>
              <LI attrLI={{ className: 'digits border-0' }}>
                <i className='icofont icofont-thumbs-up'></i>
                {item.hits}
              </LI>
              <LI attrLI={{ className: 'digits border-0' }}>
                <i className='icofont icofont-ui-chat'></i>
                {item.comments}
              </LI>
            </UL>
          </Col>
        </Row>
        <P>{item.para}</P>
      </Media>
    </Media>
  );
};

export default CommonContain;
