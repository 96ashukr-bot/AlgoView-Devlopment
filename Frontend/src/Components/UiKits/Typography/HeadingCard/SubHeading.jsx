import React from 'react';
import { Fragment } from 'react';
import { P } from '../../../../AbstractElements';
import { Heading1, Heading2, Heading3, Heading4, Heading5, Heading6, SubHeading } from '../../../../Constant';

const SubHeadings = () => {
  return (
    <Fragment>
      <P attrPara={{ className: 'h1 txt-primary' }}  >{Heading1}<small>{SubHeading}</small></P>
      <P attrPara={{ className: 'h2 txt-secondary' }}>{Heading2}<small>{SubHeading}</small></P>
      <P attrPara={{ className: 'h3 txt-success' }} >{Heading3}<small>{SubHeading}</small></P>
      <P attrPara={{ className: 'h4 txt-info' }} >{Heading4}<small>{SubHeading}</small></P>
      <P attrPara={{ className: 'h5 txt-warning' }} >{Heading5}<small>{SubHeading}</small></P>
      <P attrPara={{ className: 'h6 txt-danger' }} >{Heading6}<small>{SubHeading}</small></P>
    </Fragment>
  );
};

export default SubHeadings;