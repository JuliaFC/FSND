import React, { Component } from 'react';

import '../stylesheets/App.css';



class PageNotFound extends Component {
  constructor(){
    super();
  }

  

  render() {
    return (
      <div className="question-view">
        <div className="questions-list">
          <h2>Page Not Found</h2>
        </div>
      </div>
    );
  }
}

export default PageNotFound;
