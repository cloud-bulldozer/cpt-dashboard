// ChristmasCracker.js
import React from 'react';
import './ChristmasCracker.css';

const ChristmasCracker = () => {
  return (
    <div className="cracker" id="cracker">
      <div className="cracker-message">
        <div className="cracker-message__inner">
          Merry Xmas
          <br />
          From
          <br />
          PerfScale Team!
        </div>
      </div>
      <div className="cracker-left">
        <div className="cracker-left-inner">
          <div className="cracker-left__mask-top"></div>
          <div className="cracker-left__mask-bottom"></div>
          <div className="cracker-left__tail"></div>
          <div className="cracker-left__end"></div>
          <div className="cracker-left__body"></div>
          <div className="cracker-left-zigzag">
            <div className="cracker-left-zigzag__item"></div>
            <div className="cracker-left-zigzag__item"></div>
            <div className="cracker-left-zigzag__item"></div>
            <div className="cracker-left-zigzag__item"></div>
            <div className="cracker-left-zigzag__item"></div>
          </div>
        </div>
      </div>
      <div className="cracker-right">
        <div className="cracker-right-inner">
          <div className="cracker-right__mask-top"></div>
          <div className="cracker-right__mask-bottom"></div>
          <div className="cracker-right__tail"></div>
          <div className="cracker-right__end"></div>
          <div className="cracker-right__body"></div>
          <div className="cracker-right-zigzag">
            <div className="cracker-right-zigzag__item"></div>
            <div className="cracker-right-zigzag__item"></div>
            <div className="cracker-right-zigzag__item"></div>
            <div className="cracker-right-zigzag__item"></div>
            <div className="cracker-right-zigzag__item"></div>
          </div>
        </div>
      </div>
      <p className="hover-me-text">Hover over the Christmas cracker!</p>
    </div>
  );
};

export default ChristmasCracker;
