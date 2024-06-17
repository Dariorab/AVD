### TO-DO:
- [ ] Implementare funzionalità 
    - [ ] Sorpasso veicolo fermo o sorpasso in generale
    - [ ] mantenere distanza di sicurezza
    - [ ] vedere se e come modificare simualation del server (sincrono e con fixed time-step)
- [ ] Eventualmente modificare il PID (non è detto che ci sia bisogno)

### Problems

1. *route4*: la macchina non mantiene la distanza di sicurezza.
   Quando arriva in prossimità del veicolo (macchina della polizia) che è ferma non rallenta e la tampona
   Forse è dovuto al tipo di scenario:

   ```xml
   <scenario name="AccidentTwoWays_1" type="AccidentTwoWays">
         <trigger_point x="3710.6" y="1925.2" z="349.2" yaw="90.0"/>
         <distance value="75"/>
         <frequency from="40" to="115"/>
      </scenario>
   ```
   
   Dove per `type="AccidentTwoWays"`    
   sta per l'ego incontra un incidente, costringendolo a cambiare corsia per evitarlo ma dovendo invadere una corsia di senso opposto.

   Facendo il Debug del codice l'ego e la macchina della polizia hanno una corsia differente, però non è così, capire il motivo.

2. presenza di ostacolo statico in *route 1* `ConstructionObstacleTwoWays`, cioè l'ego incontra un'ostacolo, costringendolo a cambiare corsia per evitarlo, ma dovendo invadere una corsia di senso opposto.

*BUG*: Chiama continuamente emergency_stop() quando ha un ostacolo da superare xk la distanza è al di sotto della soglia di braking, vedere come gestire questa situazione.

### Solution
1. ...



