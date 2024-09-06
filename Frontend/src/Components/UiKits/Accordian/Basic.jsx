import React, { useState } from 'react';
import { Accordion, Col } from 'react-bootstrap';
import { Card, CardBody, CardHeader, Collapse } from 'reactstrap';
import { Btn, H5 } from '../../../AbstractElements';
import { BasicAccordion, CollapsibleGroupItem } from '../../../Constant';

const BasicAccordions = () => {
  const [isOpen, setIsOpen] = useState(1);
  const toggle = (id) => (isOpen === id ? setIsOpen(null) : setIsOpen(id));
  return (
    <Col sm="12" xl="6">
      <Accordion defaultActiveKey="0">
        <Card>
          <CardHeader>
            <H5>{BasicAccordion}</H5><span>{'Using the'} <a href="#javascript">{'card'}</a> {'component, you can extend the default collapse behavior to create an accordion.'}</span>
          </CardHeader>
          <CardBody>
            <div className="default-according" id="accordion">
              <Card>
                <CardHeader>
                  <H5 attrH5={{ className: 'mb-0' }} >
                    <Btn attrBtn={{ as: Card.Header, className: 'btn btn-link', color: 'default', onClick: () => toggle(1) }} >
                      {CollapsibleGroupItem}<span className="digits">1</span>
                    </Btn>
                  </H5>
                </CardHeader>
                <Collapse isOpen={isOpen === 1}>
                  <CardBody>
                    {'Anim pariatur cliche reprehenderit, enim eiusmod high life accusamus terry richardson ad squid. 3 wolf moon officia aute, non cupidatat skateboard dolor brunch. Food truck quinoa nesciunt laborum eiusmod. Brunch 3 wolf moon tempor, sunt aliqua put a bird on it squid single-origin coffee nulla assumenda shoreditch et.'}
                  </CardBody>
                </Collapse>
              </Card>
              <Card>
                <CardHeader>
                  <H5 attrH5={{ className: 'mb-0' }} >
                    <Btn attrBtn={{ as: Card.Header, className: 'btn btn-link', color: 'default', onClick: () => toggle(2) }} >
                      {CollapsibleGroupItem}<span className="digits">2</span>
                    </Btn>
                  </H5>
                </CardHeader>
                <Collapse isOpen={isOpen === 2}>
                  <CardBody>
                    {'Anim pariatur cliche reprehenderit, enim eiusmod high life accusamus terry richardson ad squid. 3 wolf moon officia aute, non cupidatat skateboard dolor brunch. Food truck quinoa nesciunt laborum eiusmod. Brunch 3 wolf moon tempor, sunt aliqua put a bird on it squid single-origin coffee nulla assumenda shoreditch et.'}
                  </CardBody>
                </Collapse>
              </Card>
              <Card>
                <CardHeader>
                  <H5 attrH5={{ className: 'mb-0' }} >
                    <Btn attrBtn={{ as: Card.Header, className: 'btn btn-link', color: 'default', onClick: () => toggle(3) }} >
                      {CollapsibleGroupItem}<span className="digits">3</span>
                    </Btn>
                  </H5>
                </CardHeader>
                <Collapse isOpen={isOpen === 3}>
                  <CardBody>
                    {'Anim pariatur cliche reprehenderit, enim eiusmod high life accusamus terry richardson ad squid. 3 wolf moon officia aute, non cupidatat skateboard dolor brunch. Food truck quinoa nesciunt laborum eiusmod. Brunch 3 wolf moon tempor, sunt aliqua put a bird on it squid single-origin coffee nulla assumenda shoreditch et.'}
                  </CardBody>
                </Collapse>
              </Card>
            </div>
          </CardBody>
        </Card>
      </Accordion>
    </Col>
  );
};

export default BasicAccordions;