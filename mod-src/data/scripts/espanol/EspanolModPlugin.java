package data.scripts.espanol;

import com.fs.starfarer.api.BaseModPlugin;
import com.fs.starfarer.api.Global;

public class EspanolModPlugin extends BaseModPlugin {

    @Override
    public void onGameLoad(boolean newGame) {
        // se registra despues del generador del nucleo (que se anade en
        // CoreLifecyclePluginImpl), para que sus valores tengan prioridad
        Global.getSector().getRules().addTokenReplacementGenerator(new EspanolTokens());
    }
}
