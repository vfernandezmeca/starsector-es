package data.scripts.espanol;

import java.util.HashMap;
import java.util.Map;

import com.fs.starfarer.api.campaign.CampaignFleetAPI;
import com.fs.starfarer.api.campaign.SectorEntityToken;
import com.fs.starfarer.api.campaign.rules.MemoryAPI;
import com.fs.starfarer.api.campaign.rules.RuleTokenReplacementGeneratorPlugin;
import com.fs.starfarer.api.characters.PersonAPI;
import com.fs.starfarer.api.Global;

/**
 * Traduce al espanol los tokens de genero que el juego base resuelve a
 * palabras inglesas ("he", "woman", "sir"...).
 *
 * Sin esto, una frase traducida como "$HeOrShe levanta una mano" se muestra
 * como "He levanta una mano". El mod portugues no resolvio esto y arrastra
 * ese fallo.
 *
 * Se registra despues del generador del nucleo, asi que sus valores pisan a
 * los del juego base para estas claves.
 */
public class EspanolTokens implements RuleTokenReplacementGeneratorPlugin {

    public Map<String, String> getTokenReplacements(String ruleId, Object entity,
                                                    Map<String, MemoryAPI> memoryMap) {
        Map<String, String> map = new HashMap<String, String>();

        // --- persona con la que se habla ---
        PersonAPI person = null;
        if (entity instanceof SectorEntityToken) {
            person = ((SectorEntityToken) entity).getActivePerson();
        }
        if (person == null && entity instanceof CampaignFleetAPI) {
            person = ((CampaignFleetAPI) entity).getCommander();
        }

        if (person != null) {
            boolean m = person.isMale();
            // "su" vale para los dos generos: el espanol concuerda con lo
            // poseido, no con el poseedor. 609 apariciones resueltas de golpe.
            map.put("$hisOrHer", "su");
            map.put("$HisOrHer", "Su");
            map.put("$heOrShe", m ? "\u00e9l" : "ella");
            map.put("$HeOrShe", m ? "\u00c9l" : "Ella");
            map.put("$himOrHer", m ? "\u00e9l" : "ella");
            map.put("$HimOrHer", m ? "\u00c9l" : "Ella");
            map.put("$himOrHerself", m ? "s\u00ed mismo" : "s\u00ed misma");
            map.put("$HimOrHerself", m ? "S\u00ed mismo" : "S\u00ed misma");
            map.put("$manOrWoman", m ? "hombre" : "mujer");
            map.put("$ManOrWoman", m ? "Hombre" : "Mujer");
            map.put("$brotherOrSister", m ? "hermano" : "hermana");
            map.put("$BrotherOrSister", m ? "Hermano" : "Hermana");
            map.put("$sirOrMadam", m ? "se\u00f1or" : "se\u00f1ora");
            map.put("$SirOrMadam", m ? "Se\u00f1or" : "Se\u00f1ora");
            // concordancia: permite escribir "$unUna $manOrWoman"
            map.put("$unUna", m ? "un" : "una");
            map.put("$UnUna", m ? "Un" : "Una");
            map.put("$elLa", m ? "el" : "la");
            map.put("$ElLa", m ? "El" : "La");
            map.put("$oA", m ? "o" : "a");
        }

        // --- el jugador ---
        PersonAPI p = Global.getSector().getPlayerPerson();
        if (p != null) {
            boolean m = p.isMale();
            map.put("$playerHeOrShe", m ? "\u00e9l" : "ella");
            map.put("$PlayerHeOrShe", m ? "\u00c9l" : "Ella");
            map.put("$playerHisOrHer", "su");
            map.put("$PlayerHisOrHer", "Su");
            map.put("$playerHimOrHer", m ? "\u00e9l" : "ella");
            map.put("$PlayerHimOrHer", m ? "\u00c9l" : "Ella");
            map.put("$playerManOrWoman", m ? "hombre" : "mujer");
            map.put("$PlayerManOrWoman", m ? "Hombre" : "Mujer");
            map.put("$playerSirOrMadam", m ? "se\u00f1or" : "se\u00f1ora");
            map.put("$PlayerSirOrMadam", m ? "Se\u00f1or" : "Se\u00f1ora");
            map.put("$playerUnUna", m ? "un" : "una");
            map.put("$PlayerUnUna", m ? "Un" : "Una");
            map.put("$playerElLa", m ? "el" : "la");
            map.put("$playerOA", m ? "o" : "a");
        }

        return map;
    }
}
